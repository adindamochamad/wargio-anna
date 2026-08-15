# 13 — References

Official documentation and project links. Verify URLs at implementation time — Anna docs update frequently.

---

## 13.1 Anna Developer Hub

| Resource | URL |
|----------|-----|
| Developer Hub (home) | https://anna.partners/developers |
| LLM sitemap | https://anna.partners/llms.txt |
| Full corpus | https://anna.partners/llms-full.txt |
| Markdown any page | Append `.md` to `/developers/**` URL |

---

## 13.2 Anna Core Concepts

| Doc | URL |
|-----|-----|
| Welcome | https://anna.partners/developers/overview/welcome.md |
| Concepts | https://anna.partners/developers/overview/concepts.md |
| Architecture & Lifecycle | https://anna.partners/developers/overview/architecture.md |
| Choosing What to Build | https://anna.partners/developers/overview/choosing.md |

---

## 13.3 Executa (Tools)

| Doc | URL |
|-----|-----|
| What is Executa | https://anna.partners/developers/tools/executa-intro.md |
| Python Quickstart | https://anna.partners/developers/tools/executa-python.md |
| Protocol Spec | https://anna.partners/developers/tools/executa-protocol.md |
| Lifecycle & v2 Negotiation | https://anna.partners/developers/tools/executa-lifecycle.md |
| Credentials | https://anna.partners/developers/tools/executa-credentials.md |
| Persistent Storage (APS) | https://anna.partners/developers/tools/executa-storage.md |
| Sampling (LLM reverse-RPC) | https://anna.partners/developers/tools/executa-sampling.md |
| Agent Sessions | https://anna.partners/developers/tools/executa-agent.md |
| Publishing | https://anna.partners/developers/tools/executa-publish.md |
| Common Pitfalls | https://anna.partners/developers/tools/executa-pitfalls.md |
| Cloud Agent Filesystem | https://anna.partners/developers/reference/executa-cloud-storage.md |

---

## 13.4 Anna Apps

| Doc | URL |
|-----|-----|
| What is an Anna App | https://anna.partners/developers/apps/app-intro.md |
| Quickstart (anna-app CLI) | https://anna.partners/developers/apps/app-quickstart.md |
| App Manifest | https://anna.partners/developers/apps/app-manifest.md |
| Bundling Executas | https://anna.partners/developers/apps/app-bundling.md |
| Publishing | https://anna.partners/developers/apps/app-publish.md |
| App UI Overview | https://anna.partners/developers/apps/app-ui-overview.md |
| App UI Host API | https://anna.partners/developers/apps/app-ui-host-api.md |
| App UI SDK | https://anna.partners/developers/apps/app-ui-sdk.md |
| Host API vs Executa | https://anna.partners/developers/apps/host-api-vs-executa.md |
| Local Development | https://anna.partners/developers/apps/local-dev.md |
| Local Dev with --llm | https://anna.partners/developers/apps/local-dev-llm.md |
| Testing Bundle | https://anna.partners/developers/apps/testing-bundle.md |
| Testing Plugin | https://anna.partners/developers/apps/testing-plugin.md |
| Focus Flow Example | https://anna.partners/developers/apps/app-focus-flow.md |

---

## 13.5 Reference & Legal

| Doc | URL |
|-----|-----|
| Reference index | https://anna.partners/developers/reference.md |
| Verified Developer | https://anna.partners/developers/reference/verified-developer.md |
| Developer Terms | https://anna.partners/developers/reference/developer-terms.md |
| FAQ | https://anna.partners/developers/reference/faq.md |
| anna-app CLI | https://anna.partners/developers/reference/cli.md |

---

## 13.6 Community & Program

| Resource | URL |
|----------|-----|
| Build on Anna 101 | https://forum.anna.partners/t/build-on-anna-101/228 |
| Founding Builder Program | https://forum.anna.partners/t/turn-your-ai-agents-apps-into-recurring-monthly-grants-join-the-anna-ai-os-founding-builder-program-up-to-80k-month-pool/205 |
| Developer Forum | https://forum.anna.partners/c/developers/ |

---

## 13.7 Example Repositories

| Repo | URL |
|------|-----|
| Anna Executa Examples | https://github.com/whtcjdtc2007/anna-executa-examples |
| Multi-language Anna Apps | https://github.com/whtcjdtc2007/anna-executa-examples/blob/main/docs/multi-language-anna-apps.md |
| anna-app CLI (npm) | https://www.npmjs.com/package/@anna-ai/cli |

---

## 13.8 Wargio Project

| Resource | URL / Path |
|----------|------------|
| Wargio GitHub | https://github.com/adindamochamad/wargio |
| Live demo | https://wargio.adindamochamad.com |
| Local clone | `/Users/mac/Development/wargio` |
| Deploy docs | `wargio/docs/deploy-vps.md` |
| Agent Engine setup | `wargio/docs/setup-agent-builder.md` |

---

## 13.9 OmniBridge Project

| Resource | URL |
|----------|-----|
| OmniBridge GitHub | https://github.com/adindamochamad/omnibridge |

**Status:** Second project — blocked pending Anna hardware guidance.

---

## 13.10 Wargio Anna Edition (This Project)

| Resource | Path |
|----------|------|
| Project root | `/Users/mac/Development/wargio-anna/` |
| Documentation | `/Users/mac/Development/wargio-anna/docs/` |
| Index | [00-index.md](00-index.md) |

---

## 13.11 Key Contacts & Communications

| Contact | Context |
|---------|---------|
| Jiao Li (Anna) | Recommended Wargio as first Anna App; checking OmniBridge hardware |
| Email subject | "Thought Wargio / OmniBridge could fit well with Anna App 2.0" |

---

## 13.12 Markdown Fetch Tip

For AI agents and local tooling:

```bash
# Fetch any Anna doc as markdown
curl -H 'Accept: text/markdown' https://anna.partners/developers/apps/app-manifest

# Or append .md
curl -s https://anna.partners/developers/tools/executa-intro.md
```
