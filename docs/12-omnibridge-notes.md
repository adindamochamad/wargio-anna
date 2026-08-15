# 12 — OmniBridge Notes (Second Project — Do Not Start Yet)

**Repo:** https://github.com/adindamochamad/omnibridge

---

## 12.1 What OmniBridge Is

AI agent for discovering and analyzing **legacy serial device protocols**.

```text
Physical Device
      ?
Serial / USB
      ?
Raw Bytes
      ?
AI Agent
      ?
Observe ? Hypothesize ? Probe ? Analyze
      ?
Protocol Discovery
      ?
Device Profile / Parser
```

### Conceptual Tools

- `read_more_lines`
- `search_pattern`
- `probe_baud`
- `send_bytes`
- `get_device_metadata`

---

## 12.2 Why Anna Is Interested

Jiao highlighted:

- Agentic protocol discovery
- Legacy-device analysis
- Technical differentiation

Quote:

> "OmniBridge as a very interesting second project."

---

## 12.3 Blocker: Local Hardware Access

OmniBridge relies on **local USB/serial hardware access**.

Anna Apps run in:

- User's Cloud Agent (isolated Linux microVM), or
- Local Agent on user's machine

**Problem:** Cloud Agent likely cannot access user's USB/serial devices directly.

Jiao is **checking with Anna engineering** about recommended integration architecture.

---

## 12.4 Hypothesized Future Architecture (Unconfirmed)

```text
Local Hardware Connector (user machine)
        ?
Raw serial/device data
        ?
Anna App (Local Agent only?)
        ?
AI Protocol Analysis (Executa)
```

Possible patterns (all speculative):

| Pattern | Description |
|---------|-------------|
| Local Agent only | Executa runs on machine with hardware access |
| Local bridge app | Separate connector streams bytes to Anna Executa |
| Hybrid | Cloud analysis + local capture agent |

**None confirmed.** Wait for Anna engineering guidance.

---

## 12.5 Decision

| Action | Status |
|--------|--------|
| Start OmniBridge Anna port | ? **BLOCKED** |
| Focus on Wargio Anna Edition | ? **ACTIVE** |
| Revisit after Anna hardware guidance | ? Pending |

---

## 12.6 If/When OmniBridge Proceeds

Pre-work checklist:

- [ ] Anna engineering confirms hardware integration path
- [ ] Determine Local Agent vs Cloud Agent requirements
- [ ] Map OmniBridge tools to Executa manifest
- [ ] Assess whether serial access needs separate native binary
- [ ] Review security implications of raw device byte streaming
- [ ] Separate repo/folder like wargio-anna (omnibridge-anna)

---

## 12.7 IP / Ownership

Same as Wargio per Jiao:

- OmniBridge IP remains with developer
- No exclusivity requirement
- Independent GitHub distribution continues

Verify against formal Terms before production.
