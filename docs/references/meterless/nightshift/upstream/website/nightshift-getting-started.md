# Nightshift: Getting Started (agent-ready)

> **For people:** download this file and give it to your coding agent (Claude Code, Cursor, Aider…) with the words *"Set up Nightshift on this machine using this guide."* The agent will do the checks and tell you when it needs you.
>
> **For agents:** follow the steps in order. Every step ends with a **Verify** check. Do not go to the next step until the check passes. Stop and ask the human at every **🙋 HUMAN** marker.

Full illustrated guide: [Nightshift Help](https://meterless.ai/help.html). This file works on its own; links and screenshots are optional. Questions: admin@meterless.ai.

---

## 0. Rules for the agent

1. **Never print, log or paste the runtime auth token or any cloud API key** into chat, commits or files. Refer to it through the `METERLESS_TOKEN` environment variable.
2. **Cloud API keys are typed by the human** into *Setup › Providers* in the app. Do not ask the human to paste a key to you.
3. **Do not disable security features** (SmartScreen, Gatekeeper, firewall) globally. Only allow the single prompts named below.
4. **Do not delete data.** Backup, restore and "Danger zone" actions are the human's decision.
5. A night takes minutes to hours. Submit, then poll. Do not resubmit a job because it is slow: a retried submit creates a **second** job.

---

## 1. Identify the edition

Ask or detect the OS and hardware, then pick **one** row.

| If the machine is… | Edition | Install | Endpoint for apps (8088) | `ns` CLI |
|---|---|---|---|---|
| Any computer, no install wanted | **Web** (free) | none: open `https://www.meterless.ai/Nightshift/WEB/` in desktop Chrome or Edge | No | No |
| Mac with Apple M1–M4 | **Mac M1–M4** (free) | `Nightshift-M1-M4-<version>-macos-arm64.dmg` (~30 MB) | No | No |
| Mac with Apple M5 or later | **Mac M5+** (licence) | `Nightshift-<version>-macos-arm64.dmg` | Yes | if on PATH |
| NVIDIA DGX Spark (GB10) | **DGX Spark** (on request) | release folder with `INSTALL.sh` | Yes | `/usr/bin/ns` |
| Windows 10 1809+ / 11, x64 | **Windows** (free) | `Nightshift_<version>_x64-setup.exe` (~570 MB) | Yes | `%LOCALAPPDATA%\Nightshift\cli\ns.cmd` |

Minimum memory: Windows 16 GB (32 GB+ recommended) · Mac M5+ 16 GB · DGX 64 GB (128 GB recommended) · Mac M1–M4 8 GB. Models need 2–40 GB of disk each.

**Verify:** you can name the edition. If the edition has no endpoint (Web, Mac M1–M4), skip step 4 and the CLI/API commands. Continue with the in-app job, Library and export steps.

---

## 2. Install

### Windows
1. 🙋 **HUMAN:** on meterless.ai, enter an email, verify it, press **Download for Windows**.
2. 🙋 **HUMAN:** run the `.exe` **from File Explorer** (not from inside an MSIX-packaged app). SmartScreen says "unrecognized app" because the build is unsigned: click **More info → Run anyway**.
3. The installer is per-user (no admin prompt) and installs to `%LOCALAPPDATA%\Nightshift\`. It adds WebView2 if missing.
4. 🙋 **HUMAN:** if Windows asks about port **8089** (phone pairing), allow it on **private** networks only.

**Verify (PowerShell):**
```powershell
Test-NetConnection 127.0.0.1 -Port 8088 | Select-Object TcpTestSucceeded   # True
curl.exe -s http://127.0.0.1:8088/healthz                                   # answers
& "$env:LOCALAPPDATA\Nightshift\cli\ns.cmd" status --json                   # "ok": true
```
`ns` finds the token itself (`%LOCALAPPDATA%\ai.meterless.runtime\proxy-token`). Closing the window keeps the runtime running.

### DGX Spark
```bash
cd <release-folder>
./INSTALL.sh          # checks SHA256SUMS, asks for sudo once (🙋 HUMAN types the password)
./ADD-MEDIA.sh        # optional, ~2.9 GB: image, video, speech, music engines
```
**Verify:**
```bash
systemctl status meterlessd --no-pager   # active (running)
ns status --json                         # "ok": true
ns discover --json                       # what this box can do
```

### Mac M5+
1. 🙋 **HUMAN:** open the DMG, drag **Nightshift** to Applications, right-click the app → **Open** → confirm once.
2. Wait until Setup shows **Lanes ready**. The app starts its own runtime for this user.

**Verify:** `curl -s http://127.0.0.1:8088/healthz` answers.

### Mac M1–M4
🙋 **HUMAN:** open the DMG, drag **Nightshift M1-M4** to Applications, right-click → **Open**. Needs Safari/WebKit 16.4+. **Verify:** the cockpit window opens.

### Web
Open the URL above. Pass the one-time human check (🙋 **HUMAN** if it shows a challenge). Keep the tab in the foreground while a night runs.

---

## 3. Give it models (local, cloud, or both)

The **Get started** card in **Setup** tracks compute, app connection and the first request. Finish the compute step here; the counter reaches **3/3** after a successful request. A red banner "Runtime needs attention — no compute sources configured" means compute is not ready.

**Option A — local models (free, private):**
For Web or Mac M1–M4, use the on-device fleet picker in that edition; it uses browser-engine weights, not the GGUF catalog below. For full Windows, Mac M5+ or DGX:

1. Open the Night rail **Lanes** panel (Ctrl+6 / ⌘6) → **Wide** → **Fleets**, or *Setup › Local models*. Agents with desktop control can navigate this; otherwise guide the human through the clicks.
2. Pick a fleet sized for the machine (Lite or Core for 16–32 GB) and press **Download & activate**. Missing models download for you.
3. Wait until the lane cards read **ready**.

**Option B — cloud key:**
1. 🙋 **HUMAN:** *Setup › Providers › Cloud provider keys* → **Get key ↗** on the provider → create a key → **Add** → paste → **Save**.
2. A working key reads **configured**. `rate_limited` also proves the key works. Other verdicts: `invalid_key`, `insufficient_credit`, `forbidden`, `provider_error`, `unreachable`.

**Verify (endpoint editions):**
```bash
ns discover --json            # generation: available true
```
or `GET /v1/models` with the token (see step 4) lists modes and installed models.

If a lane is refused with `insufficient_budget` or `low_live_memory`, it does not fit: close apps, stop a lane, or pick a smaller fleet size.

---

## 4. Connect an app (endpoint editions only)

Nightshift is an **OpenAI-compatible endpoint** on this machine.

| Setting | Value |
|---|---|
| Base URL | `http://127.0.0.1:8088/v1` |
| API key | the runtime auth token — 🙋 **HUMAN:** *Setup › Providers* → endpoint card → **Reveal** → **Copy**. Or press **Copy setup** for a ready recipe (curl, OpenAI SDK, Continue, Cursor, Cline/Roo, Zed, Open WebUI, LibreChat). |
| Model | `meterless/auto` (also `fast`, `deep`, `cheap`, `local`, `fusion`) |

For an agent's local test, use a process environment variable. Do not print its value or put it in a file you commit. The Windows CLI already finds the token automatically; this assignment is only needed for direct API calls:
```powershell
# Windows: read the existing local token without printing it.
$env:METERLESS_TOKEN = (Get-Content -LiteralPath "$env:LOCALAPPDATA\ai.meterless.runtime\proxy-token" -Raw).Trim()
```
```bash
# macOS / Linux: human supplies this through a local secret entry method.
# The variable must be available in the same shell that runs the test.
export METERLESS_TOKEN="<runtime token entered locally>"
```

**Verify (PowerShell):**
```powershell
$requestBody = @{ model = 'meterless/auto'; messages = @(@{ role = 'user'; content = 'Say hello in five words.' }) } | ConvertTo-Json -Depth 5
$response = Invoke-RestMethod -Uri 'http://127.0.0.1:8088/v1/chat/completions' -Method Post -ContentType 'application/json' -Headers @{ Authorization = "Bearer $env:METERLESS_TOKEN" } -Body $requestBody
$response.choices[0].message.content
```

**Verify (bash/zsh):**
```bash
curl -s http://127.0.0.1:8088/v1/chat/completions \
  -H "Authorization: Bearer $METERLESS_TOKEN" -H "Content-Type: application/json" \
  -d '{"model":"meterless/auto","messages":[{"role":"user","content":"Say hello in five words."}]}'
```
A JSON answer means it works. **401** = missing or rotated token. **Connection refused** = runtime down (step 2 verify).

```python
from openai import OpenAI
import os
client = OpenAI(base_url="http://127.0.0.1:8088/v1", api_key=os.environ["METERLESS_TOKEN"])
print(client.chat.completions.create(model="meterless/auto",
      messages=[{"role": "user", "content": "ping"}]).choices[0].message.content)
```

Other devices on the network: 🙋 **HUMAN** turns on *Setup › Preferences › Hotspot mode* **on the box itself**, and allows TCP 8088 on private networks only. LAN traffic is plain HTTP; share the token only with your own devices.

---

## 5. Queue a first job

**In the app:** Night rail **Queue** (Ctrl+2 / ⌘2). Leave **Auto** on. Write the task and what good looks like. Press **☾ Begin the night**. It waits for the quiet window (22:00 + ten idle minutes); to start now press **⚡ Begin right now**, or on the **Jobs** board (Ctrl+Shift+2) **⚡ Don't wait · run it now**.

**From the CLI (endpoint editions):**
```bash
ns generate --prompt "Write a one-page plan for <goal>. Show the arithmetic." --n 16 --json   # returns job_id
ns job watch <job_id>                      # NDJSON frames until "t":"result"
ns job outcome <job_id> --json             # accepted / rejected / undecided
ns context get <job_id> --view winner --format markdown --human
```
Exit codes: 0 ok · 2 usage · 4 not found · 6 not on this box (run `ns discover`) · 7 busy (wait `retry_after`) · 8 token · 12 runtime unreachable · 13 timeout. **Never retry `generate` automatically.**

**Verify:** the job appears on the Jobs board and reaches **Completed**; the outcome word is shown.

---

## 6. Read, find and export results

| Want to… | Where |
|---|---|
| Read the winner and the night report | Night › **☼ Morning** → **📖 Read the answer** |
| Browse every answer as cards | Night › **❖ Library** (view modes, sort, select) |
| See every past run | **Archive** (Ctrl+4 / ⌘4) |
| Export one night as a self-contained zip | Library **Workbench › ⇩ export** (or direct toolbar export on some builds) → *export with / without the prompt*; or Jobs board row menu **⇩ Export job**; or Archive inspector **⇩ Export** |
| Export every job | Jobs board **⇩ Export all**, or *Setup › Data › Export all jobs* |
| Back up the whole instance | *Setup › Data › Back up instance* (keys, tokens, models and pairing are never included) |

Extract the ZIP and open its included viewer to verify it. An exported night opens from disk or any static host, with no runtime needed. Anyone who gets the zip can read every attempt. Omitting the prompt does not remove details repeated in the answers.

---

## 7. Setup tabs at a glance

| Tab | What lives there |
|---|---|
| **Local models** | Runtime card (start/stop/restart, models folder), GPU choice (Windows), model catalog with **Download optimized** |
| **Providers** | Runtime endpoint + token, cloud provider keys (write-only) |
| **Controls** | Phone pairing (QR / code, port 8089) and what the phone may do |
| **Preferences** | Hotspot mode, local model selection, routing policy, folders, night library, hints, artifact and conversion engines |
| **Data** | Import ChatGPT/Claude history, transfer jobs, back up and restore |
| **Danger zone** | Clear chat history, reset onboarding (asks first) |

The Web edition names the first tab **Fleets** and has no Data tab.

---

## 8. Final checklist (agent reports this table to the human)

For Web and Mac M1–M4, mark endpoint and CLI checks **not applicable**. Verify that the cockpit opens, the selected compute source works, and the in-app job and export steps succeed.

| Check | How | Pass |
|---|---|---|
| Runtime up | `curl /healthz` or `ns status --json` | answers / `ok: true` |
| Compute ready | Lanes status, or `ns discover` | required lanes ready · generation available |
| App connected | curl chat completion with `$METERLESS_TOKEN` | JSON answer |
| First job | Jobs board / `ns job outcome` | Completed + outcome word |
| Export works | Library **⇩ export** | zip downloaded |

---

## 9. Quick fixes

| Symptom | Fix |
|---|---|
| "Runtime needs attention" / `ns` exit 12 | Setup › Runtime › **Restart runtime** (DGX: `sudo systemctl start meterlessd`) |
| 401 from the endpoint / `ns` exit 8 | Re-copy the token from Setup › Providers (it may have been rotated) |
| Pressed Begin, nothing runs | It waits for the quiet window: **⚡ Don't wait · run it now** |
| Lane refused `insufficient_budget` / `low_live_memory` | Smaller fleet or model, stop a lane, close apps |
| Windows: Setup › GPU shows CPU on NVIDIA | Update the GPU driver, then **Restart runtime** |
| Windows: Start-menu entry opens nothing | Re-run the installer from File Explorer |
| Another device cannot reach the hotspot | Hotspot on (on the box), firewall TCP 8088 private, same token |

Ports: 8088 API (loopback until Hotspot is on) · 11435 inference · 8089 phone.
Data: Windows `%LOCALAPPDATA%\ai.meterless.runtime\` · Mac M5+ `~/Library/Application Support/ai.meterless.runtime/` · DGX `/var/lib/meterless/`.
