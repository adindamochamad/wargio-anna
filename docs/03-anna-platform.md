# 03 — Anna Platform Concepts

**Official docs:** https://anna.partners/developers  
**Build guide:** https://forum.anna.partners/t/build-on-anna-101/228  
**LLM-friendly:** append `.md` to any `/developers/**` URL or fetch `/llms.txt`

---

## 3.1 Three Building Blocks

```text
                    Anna App
                       ?
         ?????????????????????????????
         ?             ?             ?
      Executa       SKILL.md      Listing
      (Tools)       (Skills)      Metadata
```

| Block | What | Wargio use |
|-------|------|------------|
| **Executa** | JSON-RPC 2.0 stdio plugins | **Primary** — Wargio business tools |
| **Skill** | Declarative markdown capability cards | Optional later — domain hints |
| **Anna App** | Bundle Executas + prompt + optional UI | **Primary** — Wargio Anna Edition packaging |

---

## 3.2 Executa (Tools)

Standalone process speaking **JSON-RPC 2.0 over stdio**. Anna Agent spawns it, asks what tools it provides, exposes to LLM.

### Methods

| Method | Purpose | Timeout |
|--------|---------|---------|
| `describe` | Return manifest (name, tools, parameters) | 5s |
| `invoke` | Execute one tool with arguments | 60s |
| `health` | Optional liveness | 3s |

### Critical Rules

1. **Long-running stdio server** — `for line in sys.stdin:` loop mandatory
2. **stdout = JSON-RPC only** — logs to stderr
3. **`sys.stdout.flush()`** after every response
4. **`invoke` params:** `params.tool` + `params.arguments`
5. **Success:** `{"success": true, "data": {...}}`

### Protocol v2 Capabilities (reverse-RPC)

| Capability | Purpose |
|------------|---------|
| `sampling` | LLM calls without own API key |
| `storage` | Anna Persistent Storage (APS) |
| `agent` | Multi-turn agent sessions |
| `image` | Image generation |
| `host_upload` | File upload without S3 creds |

Docs: `/developers/tools/executa-intro.md`, `/developers/tools/executa-protocol.md`

---

## 3.3 Anna App

Highest-level packaging for App Store. Bundles:

- `required_executas[]` — auto-installed on app install
- `optional_executas[]` — not auto-installed
- `system_prompt_addendum` — steers assistant when user `#mentions` app
- `user_message_prefix_template` — hint to model (placeholder not yet substituted)
- Listing metadata — name, slug, logo, screenshots (Developer Console, not in manifest zip)
- **Optional UI bundle** (`schema: 2`) — static SPA in sandboxed iframe

### Lifecycle

```text
DRAFT ? PENDING_REVIEW ? APPROVED ? PUBLISHED
                              ?
                          REJECTED ? revise
                              ?
                          ARCHIVED
```

Only `PUBLISHED` visible in App Store for new installs.

### Manifest Schema

| schema | Meaning |
|--------|---------|
| `1` | Chat-augmentation only, requires ?1 executa |
| `2` | UI runtime enabled, `ui` section allowed |

Docs: `/developers/apps/app-intro.md`, `/developers/apps/app-manifest.md`

---

## 3.4 Anna App UI (schema: 2)

Static SPA (HTML/JS/CSS) uploaded via bundle pipeline:

```text
bundle/init ? per-file PUT ? bundle/finalize
```

Rendered in sandboxed iframe. LLM can summon via `open_app_view` tool.

### Host API (from iframe)

Namespaces include:

| Namespace | Purpose |
|-----------|---------|
| `tools.*` | Call Executa from UI |
| `storage.*` | APS key-value |
| `files.*` | APS objects |
| `llm.*` | Host LLM access |
| `llm.embed` | Embeddings |
| `chat.*` | Write to conversation |
| `window.*` | Window lifecycle |
| `agent.*` | Agent sessions |

Permissions declared in `manifest.permissions` — enforced at runtime for schema: 2.

Docs: `/developers/apps/app-ui-host-api.md`, `/developers/apps/app-ui-sdk.md`

---

## 3.5 Anna Persistent Storage (APS)

Per-user durable KV + object store hosted by Anna. No cloud account needed.

### Scopes

| Scope | Owner |
|-------|-------|
| `user` | End user — cross-tool reuse |
| `app` | Anna App bundle — default |
| `tool` | Executa plugin — transient state |

### Methods

- `storage/get`, `set`, `delete`, `list`
- `files/upload_begin`, `upload_complete`, `download_url`, `list`, `delete`

**Use for Wargio:** pending payment confirmation drafts, user language preference.  
**NOT for:** full business data model (products, transactions) — too complex for KV.

Docs: `/developers/tools/executa-storage.md`

---

## 3.6 Cloud Agent Filesystem

| Path | Durability |
|------|------------|
| `$ANNA_WORKSPACE_DIR` | Persistent on Cloud Agent (`/data/workspace`) |
| `~` (home) | **Ephemeral** — wiped on image upgrade |
| APS | Survives instance destruction |

Business authoritative data ? **external MongoDB** or **APS files**.  
Workspace ? resumable working set only.

Docs: `/developers/reference/executa-cloud-storage.md`

---

## 3.7 Host API vs Executa — Decision Framework

**Default: Host API.** Use Executa when:

1. Heavy CPU/memory (PDF, embeddings, numpy)
2. Long-lived session state (DB pool, cached index)
3. Capabilities platform hasn't abstracted (external DB, private SDKs)
4. Developer-owned secrets (third-party API keys)
5. Agent-orchestrable tools (Anna Agent decides when to call)

**Executa is NOT substitute for Host API — it's extension point that should reverse-RPC back to Host API for user-scoped work.**

For Wargio:

| Need | Choice |
|------|--------|
| MongoDB access with developer credential | **Executa** |
| Pending write drafts | **APS via reverse-RPC** |
| NL reasoning | **Anna Agent** (not Executa OpenAI import) |
| Dashboard UI refresh | **Host API `tools.invoke`** |
| Product embeddings (optional) | **Host API `llm.embed`** or keep in Executa |

Docs: `/developers/apps/host-api-vs-executa.md`

---

## 3.8 Local Development

### Prerequisites

- Node.js 22+
- uv (Astral)
- `@anna-ai/cli` global

### Commands

```bash
anna-app init my-app --slug my-app
anna-app dev                    # harness at http://localhost:5180/
anna-app validate --strict
anna-app login --host https://anna.partners
anna-app doctor
```

### Local Agent

Set Local Agent as default in Anna UI before dev. Harness runs production dispatcher in-process with in-memory WindowStore.

Docs: `/developers/apps/app-quickstart.md`, `/developers/apps/local-dev.md`

---

## 3.9 Publishing

1. Publish Executa to catalogue (`tool_id`)
2. Create app version with manifest referencing published `tool_id`
3. Upload UI bundle (if schema: 2)
4. Validate manifest
5. Submit for review

Docs: `/developers/tools/executa-publish.md`, `/developers/apps/app-publish.md`

---

## 3.10 Verified Developer Program

Required for App Store listing. Activate in Developer Console.

Docs: `/developers/reference/verified-developer.md`, `/developers/reference/developer-terms.md`

---

## 3.11 Invocation Chain (Build on Anna 101)

Reference pattern for Anna Apps with LLM:

```text
App UI ? Anna Runtime ? Executa ? Reverse Sampling ? Anna LLM
```

For Wargio read tools, chain is simpler:

```text
User (#wargio) ? Anna Agent ? Wargio Executa ? MongoDB ? structured result
```

LLM reasoning happens in Anna Agent; Executa returns data, not generated prose (unless we choose to format in Executa like existing handlers do).
