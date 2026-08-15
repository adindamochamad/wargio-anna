# Wargio Anna Edition

Dokumentasi konteks dan rencana integrasi **Wargio × Anna Founding Builder Program**.

Proyek ini adalah **Anna-native distribution** dari [Wargio](https://github.com/adindamochamad/wargio). Wargio asli tetap independen dan deployable melalui GitHub/VPS.

## Status

| Fase | Status |
|------|--------|
| Analisis arsitektur | ? Selesai |
| Dokumentasi konteks | ? Selesai |
| Implementasi Anna App | ? Belum dimulai |

## Struktur Dokumentasi

| Dokumen | Isi |
|---------|-----|
| [docs/00-index.md](docs/00-index.md) | Peta navigasi semua dokumen |
| [docs/01-background-and-program.md](docs/01-background-and-program.md) | Latar belakang, email Jiao, Anna Founding Builder Program |
| [docs/02-wargio-architecture.md](docs/02-wargio-architecture.md) | Analisis lengkap repo Wargio asli |
| [docs/03-anna-platform.md](docs/03-anna-platform.md) | Konsep Anna: App, Executa, Host API, storage |
| [docs/04-compatibility-analysis.md](docs/04-compatibility-analysis.md) | Peta kompatibilitas Wargio ? Anna |
| [docs/05-target-architecture.md](docs/05-target-architecture.md) | Arsitektur target Wargio Anna Edition |
| [docs/06-migration-plan.md](docs/06-migration-plan.md) | Rencana migrasi fase demi fase |
| [docs/07-parallel-todolist.md](docs/07-parallel-todolist.md) | Todolist paralel + checkpoint |
| [docs/08-mvp-spec.md](docs/08-mvp-spec.md) | Spesifikasi MVP: 4 Executa tools |
| [docs/09-vendor-map.md](docs/09-vendor-map.md) | File Wargio yang di-reuse vs di-skip |
| [docs/10-security-and-data.md](docs/10-security-and-data.md) | Keamanan, data sintetis, tenant isolation |
| [docs/11-unresolved-questions.md](docs/11-unresolved-questions.md) | Pertanyaan teknis terbuka |
| [docs/12-omnibridge-notes.md](docs/12-omnibridge-notes.md) | Catatan proyek kedua (jangan dimulai dulu) |
| [docs/13-references.md](docs/13-references.md) | Link dokumentasi resmi |

## Prinsip Engineering

1. **Jangan rewrite** Wargio dari nol — reuse business logic.
2. **Isolasi integrasi Anna** — kode Anna-specific terpisah dari repo Wargio asli.
3. **Vertical slice dulu** — `get_inventory` end-to-end sebelum tool lain.
4. **Data sintetis** — jangan pakai production data sebelum model keamanan jelas.
5. **Jangan invent API Anna** — selalu verifikasi ke docs resmi.
6. **Submit review early** — iterasi berdasarkan feedback Anna.

## Repositori Terkait

| Repo | URL | Peran |
|------|-----|-------|
| Wargio (asli) | https://github.com/adindamochamad/wargio | Standalone product, VPS deploy |
| OmniBridge | https://github.com/adindamochamad/omnibridge | Proyek kedua — tunggu konfirmasi Anna engineering |
| Wargio Anna Edition | *(folder ini)* | Anna App + Executa + UI bundle |

## Success Criterion Pertama

```text
Anna App
  ?
User: #wargio "Produk apa yang hampir habis?"
  ?
Anna Agent ? get_inventory
  ?
Wargio Executa ? demo MongoDB
  ?
Jawaban berguna (ID/EN)
```
