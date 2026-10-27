// Application-owned memory-only bridge to the unchanged official reference.
// This integration increment does not implement durable storage or workflows.
import { createInterface } from "node:readline";
import { readFileSync } from "node:fs";
import {
  WorldModel, canonicalJson, externalId, sha256Hex,
} from "../vendor/meterless/world-model/reference/src/index.ts";
import type { Entity, WorldEvent } from "../vendor/meterless/world-model/reference/src/types.ts";

const VERSION = 1;
const MAX_REQUEST_BYTES = 4096;
const SOURCE_COMMIT = "1742dec56a66e58eef9dda2d2b865823758ca8cd";
const SYSTEM = "flood-risk-intelligence";
const VIEW = "flood-run";
type JsonObject = Record<string, unknown>;
type RunState = { revision: number; run: JsonObject | null };
type Handle = { model: WorldModel; owner: string; receipt: JsonObject; receipts?: Map<string, JsonObject> };
const runs = new Map<string, Handle>();

class CommandError extends Error {
  constructor(public code: string, message: string) { super(message); }
}
function reject(code: string, message: string): never {
  throw new CommandError(code, message);
}
function object(value: unknown): JsonObject {
  if (!value || typeof value !== "object" || Array.isArray(value))
    reject("INVALID_REQUEST", "An object is required.");
  return value as JsonObject;
}
function keys(value: JsonObject, expected: string[]): void {
  if (Object.keys(value).length !== expected.length ||
      expected.some(key => !Object.hasOwn(value, key)))
    reject("INVALID_REQUEST", "Required fields are missing or unsupported.");
}
function identifier(value: unknown): string {
  if (typeof value !== "string" || !/^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$/.test(value))
    reject("INVALID_REQUEST", "Invalid identifier.");
  return value;
}
function timestamp(value: unknown): string {
  if (typeof value !== "string" ||
      !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z$/.test(value))
    reject("INVALID_REQUEST", "A UTC timestamp is required.");
  const parsed = new Date(value);
  if (!Number.isFinite(parsed.getTime()))
    reject("INVALID_REQUEST", "Invalid timestamp.");
  const normalized = parsed.toISOString();
  if (normalized.replace(".000Z", "Z") !== value.replace(".000Z", "Z"))
    reject("INVALID_REQUEST", "Invalid calendar timestamp.");
  return normalized;
}
function analysisRequest(value: unknown, principal: string): JsonObject {
  const input = object(value);
  keys(input, [
    "userId", "requestId", "zoneId", "analysisTime",
    "forecastHorizonHours", "mode", "dataWindowStart", "dataWindowEnd",
  ]);
  const userId = identifier(input.userId);
  if (userId !== principal) reject("FORBIDDEN", "Run ownership is required.");
  const requestId = identifier(input.requestId);
  if (input.zoneId !== "LOIRE-DEMO")
    reject("INVALID_REQUEST", "This memory profile accepts the fictional demo zone only.");
  if (input.mode !== "current" && input.mode !== "historical_replay")
    reject("INVALID_REQUEST", "Unsupported analysis mode.");
  if (!Number.isSafeInteger(input.forecastHorizonHours) ||
      (input.forecastHorizonHours as number) <= 0)
    reject("INVALID_REQUEST", "A positive integer horizon is required.");
  const analysisTime = timestamp(input.analysisTime);
  const dataWindowStart = timestamp(input.dataWindowStart);
  const dataWindowEnd = timestamp(input.dataWindowEnd);
  if (!(dataWindowStart < dataWindowEnd && dataWindowEnd <= analysisTime))
    reject("INVALID_REQUEST", "The observation window is invalid.");
  return {
    userId, requestId, zoneId: input.zoneId, analysisTime,
    forecastHorizonHours: input.forecastHorizonHours, mode: input.mode,
    dataWindowStart, dataWindowEnd,
  };
}

if (process.argv.slice(2).length !== 1 || process.argv[2] !== "--memory") {
  process.stderr.write("BRIDGE_CONFIGURATION_ERROR: explicit --memory profile required.\n");
  process.exit(2);
}

let workflowText: string;
let workflow: JsonObject;
try {
  workflowText = readFileSync(new URL("../workflows/flood-analysis/1.1.0.json", import.meta.url), "utf8");
  workflow = object(JSON.parse(workflowText));
  if (workflow.workflowId !== "flood-analysis" || workflow.version !== "1.1.0")
    throw new Error("Unexpected workflow.");
} catch {
  process.stderr.write("BRIDGE_CONFIGURATION_ERROR: pinned workflow is unavailable or invalid.\n");
  process.exit(2);
}
const workflowSha256 = sha256Hex(workflowText!);
const profile = { storage: "memory", dataSource: "fixture", inference: "disabled" };

function projection(model: WorldModel): RunState {
  return model.view(VIEW).get() as RunState;
}
function registerProjection(model: WorldModel): void {
  model.registerView<RunState>(VIEW, {
    events: ["upsertEntity"],
    initialState: { revision: 0, run: null },
    reducer: (state: RunState, native: WorldEvent): RunState => {
      const entity = native.payload as Entity;
      if (entity.type !== "operation-event") return state;
      const event = entity.attrs.event as JsonObject;
      if (event.eventType === "EXECUTION_CREATED" || APP_TYPES.has(event.eventType as string))
        return reduceApplication(state, event);
      if (event.eventType !== "RUN_CREATED") return state;
      const payload = event.payload as JsonObject;
      return {
        revision: state.revision + 1,
        run: {
          runId: event.runId, userId: event.userId, requestId: event.requestId,
          workflowId: event.workflowId, workflowVersion: event.workflowVersion,
          workflowSha256: (payload.workflow as JsonObject).sha256,
          status: "CREATED", request: payload.request,
          profile: payload.profile, eventId: event.eventId,
          occurredAt: event.occurredAt, recordedAt: event.recordedAt,
        },
      };
    },
  });
}
function current(handle: Handle): JsonObject {
  return {
    state: projection(handle.model),
    nativeEventCount: handle.model.events().length,
    nativeAuditCount: handle.model.audit().length,
  };
}
function requireOwner(handle: Handle, principal: string): void {
  if (handle.owner !== principal) reject("FORBIDDEN", "Run ownership is required.");
}

async function createRun(params: JsonObject, principal: string): Promise<JsonObject> {
  keys(params, ["eventId", "runId", "request", "occurredAt", "recordedAt", "expectedRevision"]);
  const runId = identifier(params.runId);
  const existing = runs.get(runId);
  if (existing) requireOwner(existing, principal);
  const eventId = identifier(params.eventId);
  const request = analysisRequest(params.request, principal);
  const occurredAt = timestamp(params.occurredAt);
  const recordedAt = timestamp(params.recordedAt);
  if (!Number.isSafeInteger(params.expectedRevision) ||
      (params.expectedRevision as number) < 0)
    reject("INVALID_REQUEST", "A nonnegative integer revision is required.");
  const normalized = {
    eventId, runId, request, occurredAt, recordedAt,
    expectedRevision: params.expectedRevision, principalId: principal,
  };
  const command = canonicalJson(normalized);
  const entityId = externalId("operation-event", SYSTEM, eventId);
  if (existing) {
    const previous = existing.model.view("graph").entity(entityId);
    if (!previous || previous.attrs.command !== command)
      reject("EVENT_CONFLICT", "Run or event identity conflicts with its accepted command.");
    // Reconcile the original command before checking the now-newer revision.
    return { ...structuredClone(existing.receipt), duplicate: true };
  }
  if (params.expectedRevision !== 0)
    reject("REVISION_CONFLICT", "Run creation requires revision zero.");
  const namespace = "run_" + sha256Hex(runId);
  const model = new WorldModel({ storage: "memory", namespace });
  registerProjection(model);
  const event = {
    eventId, eventType: "RUN_CREATED", schemaVersion: 1,
    userId: principal, requestId: request.requestId, runId,
    workflowId: workflow!.workflowId, workflowVersion: workflow!.version,
    actorId: principal, occurredAt, recordedAt,
    payload: {
      request, profile: { ...profile },
      workflow: { definition: workflow!, sha256: workflowSha256 },
    },
  };
  await model.upsertEntity({
    type: "operation-event",
    externalKey: { system: SYSTEM, id: eventId },
    attrs: { event, command },
    source: { kind: "manual", by: principal, at: recordedAt, runId },
  });
  const handle: Handle = { model, owner: principal, receipt: {} };
  const state = current(handle);
  if (!(state.state as RunState).run)
    reject("INTERNAL_ERROR", "Run projection could not be constructed.");
  const receipt = {
    ...state, runId, namespace, eventId, nativeEntityId: entityId,
    nativeEventId: model.events()[0].id, acceptedRevision: 1, duplicate: false,
  };
  handle.receipt = structuredClone(receipt);
  runs.set(runId, handle);
  return receipt;
}


// Application-owned nominal projection; the upstream engine remains unchanged.
type AppTask = {
  taskId: string; attemptId: string; stepId: string; agentId: string;
  status: string; dependsOn: string[]; parentTaskId?: string;
};
type AppRun = JsonObject & {
  executionKind: string; tasks: Record<string, AppTask>; history: JsonObject[];
  requiresReconciliation: boolean; phase: string; status: string;
};
const APP_TYPES = new Set([
  "PROBE_CONTEXT_CREATED", "QUALIFICATION_COMPLETED", "INFERENCE_DISPATCHED",
  "INFERENCE_RESPONSE_RECEIVED", "INFERENCE_FAILED", "TOOL_REQUEST_RECEIVED",
  "DATA_REQUEST_ACCEPTED", "SQL_DISPATCHED", "DATA_OPERATION_COMPLETED",
  "DATA_OPERATION_FAILED", "TOOL_RESULT_PREPARED", "ANALYSIS_RESULT_CHECKED",
  "ANALYZER_RESULT_RECEIVED", "REPORT_PREPARED", "PROBE_FINISHED",
  "SQL_ATTEMPT_FAILED", "SQL_RETRY_SCHEDULED", "HUMAN_INTERVENTION_REQUIRED",
]);
const TERMINAL = new Set(["SUCCEEDED", "FAILED", "OUTCOME_UNKNOWN"]);
const PAYLOAD_KEYS = new Set([
  "question", "providerKind", "sourceKind", "maxInferenceCalls", "maxToolExecutions",
  "maxElapsedSeconds", "invocationId", "requestedRoute", "reportedModel",
  "verification", "errorCode", "toolCallId", "toolName", "sql", "operationId",
  "evidenceId", "rowCount", "check", "domainValidated", "analysisStatus", "outcome",
  "parentTaskId", "dataTaskId", "dataAttemptId", "resultRef",
  "nextAttemptId", "attemptNumber", "retryable", "action", "queryId", "interventionId",
]);
function appText(value: unknown, limit: number): string {
  if (typeof value !== "string" || !value.trim() || value.length > limit)
    reject("INVALID_REQUEST", "A bounded nonempty string is required.");
  return value;
}
function appProfile(value: unknown): JsonObject {
  const result = object(value);
  keys(result, ["providerKind", "sourceKind"]);
  if (!["standalone_stub", "nightshift"].includes(result.providerKind as string) ||
      !["standalone_stub", "zetaris_rest", "captured_real_snapshot"].includes(result.sourceKind as string))
    reject("INVALID_REQUEST", "Unsupported explicit dependency profile.");
  return { storage: "memory", ...result };
}
function appContext(value: unknown): JsonObject {
  const context = object(value);
  const permitted = new Set([
    "purpose", "zoneId", "analysisTime", "dataWindowStart",
    "dataWindowEnd", "forecastHorizonHours", "mode", "catalogVersion", "catalogDigest",
  ]);
  for (const [key, item] of Object.entries(context)) {
    if (!permitted.has(key) || !["string", "number"].includes(typeof item))
      reject("INVALID_REQUEST", "Unsupported execution context.");
    if (typeof item === "string") appText(item, 128);
    if (typeof item === "number" && (!Number.isFinite(item) || item <= 0))
      reject("INVALID_REQUEST", "Invalid context number.");
  }
  if (Buffer.byteLength(JSON.stringify(context), "utf8") > 768)
    reject("INVALID_REQUEST", "Execution context is too large.");
  return structuredClone(context);
}
function appEvent(value: unknown, handle: Handle, principal: string): JsonObject {
  const event = object(value);
  keys(event, [
    "eventId", "eventType", "schemaVersion", "userId", "requestId", "runId",
    "workflowId", "workflowVersion", "actorId", "occurredAt", "recordedAt",
    "stepId", "taskId", "attemptId", "agentId", "payload",
  ]);
  const run = projection(handle.model).run as AppRun;
  if (run.executionKind !== "application-execution")
    reject("INVALID_REQUEST", "This command requires an application execution.");
  identifier(event.eventId);
  for (const field of ["userId", "requestId", "runId", "actorId",
                       "stepId", "taskId", "attemptId", "agentId"])
    identifier(event[field]);
  if (event.userId !== principal || event.runId !== run.runId ||
      event.requestId !== run.requestId || event.workflowId !== run.workflowId ||
      event.workflowVersion !== run.workflowVersion)
    reject("SCOPE_CONFLICT", "Event and execution scope do not match.");
  if (event.schemaVersion !== 1 || !APP_TYPES.has(event.eventType as string))
    reject("INVALID_REQUEST", "Unsupported application event.");
  if (!["qualify-request", "analyze", "report"].includes(event.stepId as string))
    reject("INVALID_REQUEST", "Unsupported nominal workflow step.");
  const payload = object(event.payload);
  if (Buffer.byteLength(JSON.stringify(payload), "utf8") > 1024)
    reject("INVALID_REQUEST", "Event payload is too large.");
  for (const [key, item] of Object.entries(payload)) {
    if (!PAYLOAD_KEYS.has(key) || (item !== null &&
        !["string", "number", "boolean"].includes(typeof item)))
      reject("INVALID_REQUEST", "Unsupported event payload field.");
    if (typeof item === "number" && !Number.isFinite(item))
      reject("INVALID_REQUEST", "Finite payload values are required.");
  }
  return { ...structuredClone(event), occurredAt: timestamp(event.occurredAt),
           recordedAt: timestamp(event.recordedAt) };
}
function taskFor(run: AppRun, event: JsonObject): AppTask {
  const id = identifier(event.taskId);
  const existing = run.tasks[id];
  if (existing) {
    if (existing.stepId !== event.stepId)
      reject("TASK_CONFLICT", "Task identity cannot change its step.");
    if (existing.attemptId !== event.attemptId) {
      if (run.workflowVersion !== "1.3.0" || event.eventType !== "SQL_DISPATCHED" ||
          existing.status !== "RETRY_PENDING" || existing.nextAttemptId !== event.attemptId)
        reject("TASK_CONFLICT", "A new attempt requires an admitted read-only retry.");
      existing.attemptId = identifier(event.attemptId);
      delete existing.nextAttemptId;
    }
    return existing;
  }
  const payload = event.payload as JsonObject;
  const parent = payload.parentTaskId ? identifier(payload.parentTaskId) : undefined;
  if (parent && !run.tasks[parent])
    reject("DEPENDENCY_CONFLICT", "The parent task must exist.");
  let dependsOn: string[] = [];
  if (!parent && event.stepId !== "qualify-request") {
    const needed = event.stepId === "analyze" ? "qualify-request" : "analyze";
    const previous = Object.values(run.tasks).find(t => t.stepId === needed && !t.parentTaskId);
    if (!previous || previous.status !== "COMPLETED")
      reject("DEPENDENCY_CONFLICT", "The prior nominal step must be completed.");
    dependsOn = [previous.taskId];
  }
  const task: AppTask = {
    taskId: id, attemptId: identifier(event.attemptId),
    stepId: identifier(event.stepId), agentId: identifier(event.agentId),
    status: "RUNNING", dependsOn,
    ...(parent ? { parentTaskId: parent } : {}),
  };
  run.tasks[id] = task;
  return task;
}
function attemptsFor(task: AppTask): Record<string, JsonObject> {
  if (!task.attempts) task.attempts = {};
  return task.attempts as Record<string, JsonObject>;
}
function reduceApplication(state: RunState, event: JsonObject): RunState {
  if (event.eventType === "EXECUTION_CREATED") {
    const payload = event.payload as JsonObject;
    const workflow = payload.workflow as JsonObject;
    return { revision: state.revision + 1, run: {
      executionKind: "application-execution",
      runId: event.runId, userId: event.userId, requestId: event.requestId,
      workflowId: event.workflowId, workflowVersion: event.workflowVersion,
      workflowSha256: workflow.sha256, question: payload.question,
      context: payload.context, profile: payload.profile,
      status: "CREATED", phase: "qualify-request", requiresReconciliation: false,
      tasks: {}, history: [{ eventId: event.eventId, eventType: event.eventType,
                            recordedAt: event.recordedAt }],
    } };
  }
  if (!APP_TYPES.has(event.eventType as string)) return state;
  if (!state.run || state.run.executionKind !== "application-execution")
    reject("INVALID_REQUEST", "Application execution is missing.");
  const run = structuredClone(state.run) as AppRun;
  if (TERMINAL.has(run.status)) reject("TERMINAL_STATE", "Execution is already closed.");
  if (run.history.length >= 32) reject("EVENT_BUDGET_EXHAUSTED", "Execution event budget exceeded.");
  const payload = event.payload as JsonObject;
  const type = event.eventType as string;
  const modern = run.workflowVersion === "1.3.0";
  const incidentTypes = ["SQL_ATTEMPT_FAILED", "SQL_RETRY_SCHEDULED", "HUMAN_INTERVENTION_REQUIRED"];
  if (!modern && incidentTypes.includes(type))
    reject("WORKFLOW_POLICY_CONFLICT", "This event requires workflow 1.3.0.");
  if (run.status === "WAITING_HUMAN" && (type !== "PROBE_FINISHED" || run.suspensionRecorded))
    reject("HUMAN_INTERVENTION_REQUIRED", "Human intervention is pending; no new dispatch is allowed.");
  if (type === "PROBE_FINISHED") {
    if (payload.outcome === "WAITING_HUMAN") {
      if (!modern || run.status !== "WAITING_HUMAN" || !run.humanIntervention)
        reject("DEPENDENCY_CONFLICT", "A scoped intervention request is required.");
      run.phase = "human-intervention";
      run.suspensionRecorded = true;
    } else {
      if (payload.outcome !== "PASSED" && payload.outcome !== "FAILED")
        reject("INVALID_REQUEST", "Invalid probe outcome.");
      if (payload.outcome === "PASSED") {
        const steps = ["qualify-request", "analyze", "report"];
        if (run.requiresReconciliation || !steps.every(step =>
            Object.values(run.tasks).some(t => t.stepId === step && !t.parentTaskId &&
                                           t.status === "COMPLETED")) ||
            Object.values(run.tasks).some(t => t.status !== "COMPLETED"))
          reject("DEPENDENCY_CONFLICT", "Required nominal tasks are not complete.");
        run.status = "SUCCEEDED";
      } else {
        run.status = run.requiresReconciliation ? "OUTCOME_UNKNOWN" : "FAILED";
        for (const task of Object.values(run.tasks))
          if (task.status !== "COMPLETED")
            task.status = run.requiresReconciliation ? "OUTCOME_UNKNOWN" : "FAILED";
      }
      run.phase = "closed";
    }
  } else {
    const task = taskFor(run, event);
    run.status = "RUNNING";
    if (type === "QUALIFICATION_COMPLETED") {
      if (event.stepId !== "qualify-request")
        reject("INVALID_REQUEST", "Qualification belongs to its nominal step.");
      task.status = "COMPLETED";
      run.phase = "analyze";
    } else if (type === "DATA_REQUEST_ACCEPTED") {
      const parent = run.tasks[identifier(payload.parentTaskId)];
      if (!parent || parent.stepId !== "analyze")
        reject("DEPENDENCY_CONFLICT", "An Analyzer parent task is required.");
      if (modern) {
        if (task.operationId) reject("ATTEMPT_CONFLICT", "The data operation already exists.");
        task.operationId = identifier(payload.operationId);
        task.attempts = {};
      }
      parent.status = "WAITING_DATA";
    } else if (modern && type === "SQL_DISPATCHED") {
      if (!task.parentTaskId || payload.operationId !== task.operationId)
        reject("SCOPE_CONFLICT", "The attempt must belong to its data operation.");
      const attempts = attemptsFor(task);
      const expected = Object.keys(attempts).length + 1;
      if (expected > 2 || payload.attemptNumber !== expected || attempts[task.attemptId])
        reject("ATTEMPT_CONFLICT", "Only two distinct ordered SQL attempts are admitted.");
      attempts[task.attemptId] = { attemptId: task.attemptId, status: "RUNNING",
                                  number: expected, queryId: payload.queryId };
      task.status = "RUNNING";
    } else if (type === "SQL_ATTEMPT_FAILED") {
      const active = attemptsFor(task)[task.attemptId];
      if (!active || active.status !== "RUNNING" || active.number !== 1 ||
          payload.operationId !== task.operationId || payload.retryable !== true ||
          !["ZETARIS_OUTCOME_UNKNOWN", "ZETARIS_TRANSIENT_HTTP_ERROR"].includes(payload.errorCode as string))
        reject("ATTEMPT_CONFLICT", "No admitted first read can be retried.");
      active.status = (payload.errorCode as string).includes("UNKNOWN") ? "OUTCOME_UNKNOWN" : "FAILED";
      active.errorCode = payload.errorCode;
      task.status = "RETRY_PENDING";
    } else if (type === "SQL_RETRY_SCHEDULED") {
      if (task.status !== "RETRY_PENDING" || task.nextAttemptId ||
          Object.keys(attemptsFor(task)).length !== 1 || payload.operationId !== task.operationId ||
          payload.attemptNumber !== 2)
        reject("ATTEMPT_CONFLICT", "Only one retry may be scheduled.");
      const next = identifier(payload.nextAttemptId);
      if (next === task.attemptId) reject("ATTEMPT_CONFLICT", "A retry needs a distinct attempt identity.");
      task.nextAttemptId = next;
      attemptsFor(task)[task.attemptId].supersededByReadAttempt = next;
    } else if (type === "DATA_OPERATION_COMPLETED") {
      if (modern) {
        const active = attemptsFor(task)[task.attemptId];
        if (!active || active.status !== "RUNNING" || payload.operationId !== task.operationId)
          reject("ATTEMPT_CONFLICT", "Only the active read attempt can complete.");
        active.status = "COMPLETED";
        active.evidenceId = payload.evidenceId;
      }
      task.status = "COMPLETED";
      if (task.parentTaskId) run.tasks[task.parentTaskId].status = "RUNNING";
    } else if (type === "HUMAN_INTERVENTION_REQUIRED") {
      if (!task.parentTaskId || !["FAILED", "OUTCOME_UNKNOWN"].includes(task.status as string) ||
          payload.operationId !== task.operationId ||
          payload.action !== "CHECK_SOURCE_AND_RESTART_EXPLICITLY")
        reject("DEPENDENCY_CONFLICT", "A failed scoped data operation is required.");
      task.status = "WAITING_HUMAN";
      run.tasks[task.parentTaskId].status = "WAITING_HUMAN";
      run.status = "WAITING_HUMAN";
      run.phase = "human-intervention";
      run.humanIntervention = {
        interventionId: identifier(payload.interventionId), userId: run.userId,
        runId: run.runId, requestId: run.requestId, taskId: task.taskId,
        attemptId: task.attemptId, operationId: task.operationId,
        reason: payload.errorCode, action: payload.action, requestedAt: event.recordedAt,
      };
    } else if (type === "ANALYZER_RESULT_RECEIVED") {
      if (Object.values(run.tasks).some(t => t.parentTaskId === task.taskId && t.status !== "COMPLETED"))
        reject("DEPENDENCY_CONFLICT", "Required data tasks remain incomplete.");
      task.status = "COMPLETED";
      run.phase = "report";
    } else if (type === "REPORT_PREPARED") {
      if (event.stepId !== "report") reject("INVALID_REQUEST", "A report step is required.");
      task.status = "COMPLETED";
    } else if (type === "INFERENCE_FAILED" || type === "DATA_OPERATION_FAILED") {
      const uncertain = typeof payload.errorCode === "string" && payload.errorCode.includes("UNKNOWN");
      run.requiresReconciliation ||= uncertain;
      task.status = uncertain ? "OUTCOME_UNKNOWN" : "FAILED";
      if (modern && type === "DATA_OPERATION_FAILED") {
        const active = attemptsFor(task)[task.attemptId];
        if (active && active.status === "RUNNING") {
          active.status = task.status;
          active.errorCode = payload.errorCode;
        }
      }
    }
  }
  run.history.push({
    eventId: event.eventId, eventType: type, taskId: event.taskId,
    stepId: event.stepId, recordedAt: event.recordedAt, payload,
  });
  return { revision: state.revision + 1, run };
}
function applicationWorkflow(version = "1.2.0"): { definition: JsonObject; sha256: string } {
  if (!["1.2.0", "1.3.0"].includes(version))
    reject("INVALID_REQUEST", "Unsupported application workflow version.");
  const text = readFileSync(new URL("../workflows/flood-analysis/" + version + ".json", import.meta.url), "utf8");
  const definition = object(JSON.parse(text));
  if (definition.workflowId !== "flood-analysis" || definition.version !== version)
    reject("INTERNAL_ERROR", "The pinned application workflow is invalid.");
  return { definition, sha256: sha256Hex(text) };
}
async function createExecution(params: JsonObject, principal: string): Promise<JsonObject> {
  keys(params, ["eventId", "runId", "userId", "requestId", "question", "context",
                "profile", "occurredAt", "recordedAt", "expectedRevision",
                ...(params.workflowVersion !== undefined ? ["workflowVersion"] : [])]);
  const runId = identifier(params.runId);
  const existing = runs.get(runId);
  if (existing) requireOwner(existing, principal);
  if (identifier(params.userId) !== principal)
    reject("FORBIDDEN", "Execution ownership is required.");
  const normalized = {
    eventId: identifier(params.eventId), runId, userId: principal,
    requestId: identifier(params.requestId), question: appText(params.question, 512),
    context: appContext(params.context), profile: appProfile(params.profile),
    workflowVersion: appText(params.workflowVersion ?? "1.2.0", 16),
    occurredAt: timestamp(params.occurredAt), recordedAt: timestamp(params.recordedAt),
    expectedRevision: params.expectedRevision, principalId: principal,
  };
  if (!Number.isSafeInteger(params.expectedRevision) || (params.expectedRevision as number) < 0)
    reject("INVALID_REQUEST", "A nonnegative revision is required.");
  const command = canonicalJson(normalized);
  const entityId = externalId("operation-event", SYSTEM, normalized.eventId);
  if (existing) {
    const previous = existing.model.view("graph").entity(entityId);
    if (!previous || previous.attrs.command !== command)
      reject("EVENT_CONFLICT", "Execution identity conflicts with its original command.");
    return { ...structuredClone(existing.receipt), duplicate: true };
  }
  if (params.expectedRevision !== 0) reject("REVISION_CONFLICT", "Creation requires revision zero.");
  const namespace = "run_" + sha256Hex(runId);
  const model = new WorldModel({ storage: "memory", namespace });
  registerProjection(model);
  const pinned = applicationWorkflow(normalized.workflowVersion);
  const event = {
    eventId: normalized.eventId, eventType: "EXECUTION_CREATED", schemaVersion: 1,
    userId: principal, requestId: normalized.requestId, runId,
    workflowId: "flood-analysis", workflowVersion: normalized.workflowVersion, actorId: principal,
    occurredAt: normalized.occurredAt, recordedAt: normalized.recordedAt,
    payload: { question: normalized.question, context: normalized.context,
               profile: normalized.profile, workflow: pinned },
  };
  await model.upsertEntity({
    type: "operation-event", externalKey: { system: SYSTEM, id: normalized.eventId },
    attrs: { event, command },
    source: { kind: "manual", by: principal, at: normalized.recordedAt, runId },
  });
  const handle: Handle = { model, owner: principal, receipt: {}, receipts: new Map() };
  const receipt = {
    runId, namespace, eventId: normalized.eventId, ...current(handle),
    nativeEntityId: entityId, nativeEventId: model.events().at(-1)!.id,
    acceptedRevision: 1, duplicate: false,
  };
  handle.receipt = structuredClone(receipt);
  runs.set(runId, handle);
  return receipt;
}
async function appendEvent(params: JsonObject, principal: string): Promise<JsonObject> {
  keys(params, ["runId", "event", "expectedRevision"]);
  const runId = identifier(params.runId);
  const handle = runs.get(runId);
  if (!handle) reject("RUN_NOT_FOUND", "Execution is unavailable.");
  requireOwner(handle, principal);
  const event = appEvent(params.event, handle, principal);
  if (!Number.isSafeInteger(params.expectedRevision) || (params.expectedRevision as number) < 0)
    reject("INVALID_REQUEST", "A nonnegative revision is required.");
  const command = canonicalJson({ runId, event, expectedRevision: params.expectedRevision, principalId: principal });
  const entityId = externalId("operation-event", SYSTEM, event.eventId as string);
  const previous = handle.model.view("graph").entity(entityId);
  if (previous) {
    if (previous.attrs.command !== command || !handle.receipts?.has(event.eventId as string))
      reject("EVENT_CONFLICT", "Event identity conflicts with its original command.");
    return { ...structuredClone(handle.receipts.get(event.eventId as string)!), duplicate: true };
  }
  const state = projection(handle.model);
  if (params.expectedRevision !== state.revision)
    reject("REVISION_CONFLICT", "Execution revision has changed.");
  // Validate application transitions before asking the official engine to mutate.
  reduceApplication(state, event);
  await handle.model.upsertEntity({
    type: "operation-event", externalKey: { system: SYSTEM, id: event.eventId as string },
    attrs: { event, command },
    source: { kind: "agent", by: event.actorId as string, at: event.recordedAt as string, runId },
  });
  const receipt = {
    runId, namespace: "run_" + sha256Hex(runId), eventId: event.eventId,
    ...current(handle), nativeEntityId: entityId,
    nativeEventId: handle.model.events().at(-1)!.id,
    acceptedRevision: state.revision + 1, duplicate: false,
  };
  handle.receipts!.set(event.eventId as string, structuredClone(receipt));
  return receipt;
}

async function dispatch(frame: JsonObject): Promise<JsonObject> {
  keys(frame, ["protocolVersion", "messageId", "principalId", "command", "params"]);
  if (frame.protocolVersion !== VERSION)
    reject("INVALID_REQUEST", "Unsupported protocol version.");
  identifier(frame.messageId);
  const principal = identifier(frame.principalId);
  const params = object(frame.params);
  switch (frame.command) {
    case "ping":
      keys(params, []);
      return {
        protocolVersion: VERSION, profile, namespaces: runs.size,
        engine: { package: "@meterless/world-model-reference", version: "0.1.0", commit: SOURCE_COMMIT },
      };
    case "create_run":
      return createRun(params, principal);
    case "create_execution":
      return createExecution(params, principal);
    case "append_event":
      return appendEvent(params, principal);
    case "get_run": {
      keys(params, ["runId"]);
      const runId = identifier(params.runId);
      const handle = runs.get(runId);
      if (!handle) reject("RUN_NOT_FOUND", "Run is unavailable.");
      requireOwner(handle, principal);
      return { runId, namespace: "run_" + sha256Hex(runId), ...current(handle) };
    }
    case "shutdown":
      keys(params, []);
      return { stopped: true };
    default:
      reject("UNKNOWN_COMMAND", "Unsupported bridge command.");
  }
}

// The caller context is supplied by the trusted local application.
// Owner checks are simulated prototype controls, not external authentication.
const input = createInterface({ input: process.stdin, crlfDelay: Infinity });
for await (const line of input) {
  let messageId: string | null = null;
  let shutdown = false;
  let response: JsonObject;
  try {
    if (Buffer.byteLength(line, "utf8") + 1 > MAX_REQUEST_BYTES)
      reject("INVALID_REQUEST", "Request exceeds the protocol limit.");
    let parsed: unknown;
    try { parsed = JSON.parse(line); }
    catch { reject("INVALID_JSON", "A JSON object is required."); }
    const frame = object(parsed);
    if (typeof frame.messageId === "string" &&
        /^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$/.test(frame.messageId))
      messageId = frame.messageId;
    const result = await dispatch(frame);
    shutdown = frame.command === "shutdown";
    response = { protocolVersion: VERSION, messageId, ok: true, result };
  } catch (error) {
    const known = error instanceof CommandError;
    if (!known) process.stderr.write("BRIDGE_INTERNAL_ERROR\n");
    response = {
      protocolVersion: VERSION, messageId, ok: false,
      error: {
        code: known ? error.code : "INTERNAL_ERROR",
        message: known ? error.message : "Bridge operation failed.",
      },
    };
  }
  process.stdout.write(JSON.stringify(response) + "\n");
  if (shutdown) {
    input.close();
    process.stdin.pause();
    break;
  }
}

// History: 2026-10-27: Added memory-only application execution events and nominal projections while preserving E1 commands.

// History: 2026-10-27: Added scoped catalog-aware hydro analysis while retaining the SELECT-one baseline and explicit dependency profiles.

// History: 2026-10-27: Added explicit workflow 1.3 read attempts and scoped human-intervention projection; legacy profiles retained.
