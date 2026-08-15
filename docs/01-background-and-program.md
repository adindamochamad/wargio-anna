# 01 — Background & Anna Founding Builder Program

## 1.1 Latar Belakang

Developer/creator dari dua proyek open-source:

| Proyek | URL |
|--------|-----|
| **Wargio** | https://github.com/adindamochamad/wargio |
| **OmniBridge** | https://github.com/adindamochamad/omnibridge |

Kontak langsung dari **Jiao Li** (Anna) terkait **Anna Founding Builder Program**.

**Subject email:**

> "Thought Wargio / OmniBridge could fit well with Anna App 2.0"

Ini bukan outreach generik. Jiao secara eksplisit mereview Wargio dan OmniBridge, dan merekomendasikan **Wargio sebagai Anna App pertama**, dengan OmniBridge sebagai kandidat proyek kedua.

---

## 1.2 Anna Founding Builder Program

Anna adalah **AI OS / AI agent platform** tempat developer mengubah agents, tools, scripts, workflows, dan produk AI existing menjadi **Apps** yang user jalankan melalui Anna.

Program Founding Builder menawarkan **recurring monthly grants** berdasarkan primarily **Qualified MAU**.

### Tier Grant (published)

| Qualified MAU | Monthly Grant |
|--------------:|--------------:|
| 200+ | $50 |
| 500+ | $100 |
| 1,000+ | $200 |
| 4,000+ | $1,000 |
| 10,000+ | $2,500 |
| 20,000+ | $5,000 |

Funding pool bulanan: hingga **$80,000/month** (advertised).

### Definisi Qualified MAU

MAU **bukan** sekadar app opens atau installs. Qualified MAU harus:

- User Anna yang **valid signed-in**
- Melakukan **meaningful successful app run**

### Syarat App

- Pass **App Review**
- Published sebagai **Marketplace App** nyata
- Tetap **functional**
- Provide **meaningful utility**
- **Maintained/improved**
- Comply dengan fair-play dan program rules

### Timeline Program

- **Agustus 2026:** build/beta period
- **September 2026:** qualification window starts

Workflow yang diencourage:

```text
Build ? Review ? Feedback ? Iterate
```

---

## 1.3 Rekomendasi Jiao untuk Wargio

Yang menarik perhatian Anna:

- AI-agent architecture
- Tools
- Business logic
- Real user-facing workflow

Keyakinan: maps naturally ke Anna, relatively fast path ke Marketplace App.

**Quote:**

> "I'd recommend Wargio as the first Anna App, with OmniBridge as a very interesting second project."

---

## 1.4 Rekomendasi Jiao untuk OmniBridge

Highlight:

- Agentic protocol discovery
- Legacy-device analysis
- Technical differentiation

**Blocker:** OmniBridge bergantung pada **local USB/serial hardware access**. Jiao sedang check dengan Anna engineering tentang recommended integration architecture.

**Keputusan:** Jangan mulai port OmniBridge sampai Anna engineering confirm path hardware access.

---

## 1.5 IP / Ownership (dari Jiao)

| Poin | Status |
|------|--------|
| Existing project ownership | Tetap dengan developer |
| Existing IP | Tetap milik developer |
| Anna-native version | Tidak transfer ownership ke Anna |
| Exclusivity | Tidak ada requirement |
| Independent distribution | Boleh continue GitHub, website, platform lain |

**Catatan:** Berdasarkan respons tertulis Jiao. Sebelum production dengan proprietary code/data, tetap inspect **Anna formal Terms / Builder Agreement**.

---

## 1.6 Data Architecture (dari Anna)

Anna Apps run inside user's **Agent environment**.

Untuk **Anna Cloud Agent**, setiap user dapat isolated Linux environment.

Tidak perlu migrate seluruh Wargio data architecture ke shared Anna backend — perlu investigate:

- User isolation
- Business data persistence
- Retention, deletion, backup, export
- Authentication, permissions
- External database connectivity

**Rule:** Jangan pakai real production/business data selama initial integration. Gunakan **synthetic/demo data**.

---

## 1.7 Product Strategy

Jangan optimize untuk $5,000 segera. Goal pertama: **technical feasibility**.

```text
Working Anna App
    ?
5 successful users
    ?
20 recurring users
    ?
100 users
    ?
200 Qualified MAU
    ?
500 MAU
    ?
1,000 MAU
```

Grant = consequence of useful product, bukan primary requirement.

**Keunggulan Wargio untuk MAU:**

Use case naturally recurring:

- Checking inventory
- Checking sales
- Checking debt
- Recording payments
- Restocking
- Weekly business reports

Lebih cocok untuk MAU-based rewards daripada one-time utility.

---

## 1.8 Prioritas Immediate

**Bukan:**

- Redesign Wargio
- Rewrite all backend
- Implement every feature
- Optimize for 20,000 MAU
- Port OmniBridge
- Migrate production data

**Ya:**

```text
Anna App
  ?
User asks real Wargio question
  ?
Anna Agent reasons
  ?
Wargio tool executes
  ?
Business data queried
  ?
Useful answer returned
```
