"""Standalone client tests: injected wire responses, no Node or network."""
import unittest

from agent.world_model import (
    BridgeCommandError, BridgeOutcomeUnknown, BridgeProtocolError, WorldModelClient,
)


class StubTransport:
    def __init__(self, respond):
        self.respond = respond
        self.calls = []
        self.closed = False

    def exchange(self, frame):
        self.calls.append(frame)
        return self.respond(frame)

    def close(self):
        self.closed = True


def success(frame):
    return {
        "protocolVersion": 1, "messageId": frame["messageId"],
        "ok": True, "result": {"marker": "standalone"},
    }


class ClientTests(unittest.TestCase):
    def test_explicit_stub_returns_result_and_keeps_context_separate(self):
        stub = StubTransport(success)
        with WorldModelClient(stub) as client:
            result = client.get_run("RUN-001", principal_id="USR-001")
        self.assertEqual(result, {"marker": "standalone"})
        self.assertEqual(stub.calls[0]["principalId"], "USR-001")
        self.assertEqual(stub.calls[0]["params"], {"runId": "RUN-001"})
        self.assertTrue(stub.closed)

    def test_rejected_command_is_not_retried(self):
        def reject(frame):
            return {
                "protocolVersion": 1, "messageId": frame["messageId"], "ok": False,
                "error": {"code": "FORBIDDEN", "message": "Run ownership is required."},
            }
        stub = StubTransport(reject)
        with WorldModelClient(stub) as client:
            with self.assertRaises(BridgeCommandError) as caught:
                client.get_run("RUN-001", principal_id="USR-002")
        self.assertEqual(caught.exception.code, "FORBIDDEN")
        self.assertEqual(len(stub.calls), 1)

    def test_wrong_correlation_disables_client(self):
        def mismatch(frame):
            response = success(frame)
            response["messageId"] = "OTHER"
            return response
        stub = StubTransport(mismatch)
        with WorldModelClient(stub) as client:
            with self.assertRaises(BridgeProtocolError):
                client.ping(principal_id="USR-001")
            with self.assertRaises(BridgeProtocolError):
                client.ping(principal_id="USR-001")
        self.assertEqual(len(stub.calls), 1)

    def test_write_timeout_reports_uncertain_outcome_without_retry(self):
        def timeout(_):
            raise TimeoutError("Controlled standalone timeout.")
        stub = StubTransport(timeout)
        with WorldModelClient(stub) as client:
            with self.assertRaises(BridgeOutcomeUnknown):
                client.create_run(principal_id="USR-001", runId="RUN-001")
            with self.assertRaises(BridgeProtocolError):
                client.ping(principal_id="USR-001")
        self.assertEqual(len(stub.calls), 1)

    def test_oversized_input_is_rejected_before_transport(self):
        stub = StubTransport(success)
        with WorldModelClient(stub) as client:
            with self.assertRaises(ValueError):
                client.create_run(principal_id="USR-001", text="x" * 5000)
        self.assertEqual(stub.calls, [])

    def test_nonfinite_json_is_rejected_before_transport(self):
        stub = StubTransport(success)
        with WorldModelClient(stub) as client:
            with self.assertRaises(ValueError):
                client.create_run(principal_id="USR-001", value=float("nan"))
        self.assertEqual(stub.calls, [])

    def test_context_manager_closes_after_caller_failure(self):
        stub = StubTransport(success)
        with self.assertRaises(RuntimeError):
            with WorldModelClient(stub):
                raise RuntimeError("Controlled caller failure.")
        self.assertTrue(stub.closed)

    def test_write_transport_loss_reports_uncertain_outcome(self):
        def lost(_):
            raise BridgeProtocolError("Controlled connection loss.")
        stub = StubTransport(lost)
        with WorldModelClient(stub) as client:
            with self.assertRaises(BridgeOutcomeUnknown):
                client.create_run(principal_id="USR-001", runId="RUN-001")
        self.assertEqual(len(stub.calls), 1)

    def test_malformed_write_acknowledgement_is_not_treated_as_rejection(self):
        stub = StubTransport(lambda _: {"unexpected": True})
        with WorldModelClient(stub) as client:
            with self.assertRaises(BridgeOutcomeUnknown):
                client.create_run(principal_id="USR-001", runId="RUN-001")
        self.assertEqual(len(stub.calls), 1)
