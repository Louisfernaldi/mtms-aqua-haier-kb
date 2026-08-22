# ESTAFET — Galeri & Insight Engine (2026-08-21)
Aturan: paralel CUMA kalau nol irisan file_disentuh · nyangkut = LOMPAT ke tiket berikutnya · gerbang_acc = STOP siap-tekan, mandor ga pernah menekan · receipt 6-field ke `evidence\<id>\receipt.md` · ACC deploy = fresh dari Louis di sesi eksekusi.

| id | tiket | status | owner | verifier | depends | catatan |
|----|-------|--------|-------|----------|---------|---------|
| 01 | pipeline-gfk | kelar | codex | claude-mandor | [] | LULUS: 47 brand/7 region/13 kelas; kontrol AQUA .1467 cocok; sabotase merah->hijau; evidence t01 |
| 02 | halaman-peta-pasar | kelar | codex | claude-mandor | [01] | LULUS: 3 panel dari JSON, nol hardcode, headless PASS; bug favicon 404 ditambal akar; evidence t02 |
| 03 | login-gate | kelar-siap-ketok | codex | claude-mandor | [] | middleware dibalik (locked=/pasar,/benchmark,/strategi); statis lulus (nol hardcode, auth utuh); runtime wrangler KEBLOKIR WinError32 miniflare = transport, bukti live ikut T12 |
| 04 | pipeline-galeri-v2 | kelar | codex | claude-mandor | [] | LULUS: 323=323, sabotase merah->hijau; OCR 0% (paket winrt belum terpasang - opsional, script siap retry) |
| 05 | galeri-museum-ui | kelar | codex | claude-mandor | [04] | LULUS: img=323 pas, search jalan, lightbox OK, mobile 390 aman, sabotase merah; OCR search terpasang nunggu cache terisi |
| 06 | file-auto-render | kelar | codex | claude-mandor | [] | LULUS: bug to-top ketemu audit, ditambal akar; headless 27 item, nol error console |
| 07 | halaman-benchmark | kelar | codex | claude-mandor | [] | LULUS: 229 model (58 AQUA, 13 brand, 93 berharga); spot-check AQR-D205 cocok sumber; nol hardcode; sabotase merah->hijau |
| 08 | strategi-ceo | kelar | claude-mandor | pembukti | [01] | LULUS: pipeline_strategi.py angka mesin dari GFK; sabotase v2 merah->hijau (v1 tautologi ketangkap + difix akar); headless PASS; narasi analis Sharleen; evidence t08 |
| 09 | poster-b2b | kelar | claude-mandor | pembukti | [07] | LULUS: 12 poster (4 lini x feed/story/A4) idempoten hash; juri buta-niat 4/4 setelah fix footer ronde 1; angka kulkas dari benchmark JSON; catatan: foto produk asli nol di repo -> background AI abstrak + overlay kode; evidence t09 |
| 10 | pipeline-update-semua | kelar | codex | claude-mandor | [01,04,06,07] | LULUS: 4 pipeline hijau 1-perintah; sabotase exit1+sebut merahnya; idempoten |
| 11 | integrasi-nav | kelar | claude-mandor | pembukti | [02,05,07,08,09] | LULUS: 12/13 html nav 12 link (login 0), index 10 kartu (6+4), headless index+galeri 0 error 0 h-scroll @390/1280, style.css tidak tersentuh; evidence t11 |
| 12 | deploy-live | kelar | claude-mandor | pembukti | [03,10,11] | LULUS: Pages 1c55076c 52 baru/598 cached -> master.mtms-aqua-haier-kb.pages.dev; gate 302 OK (3 locked), 308->200 public; T11 masih ANTRE tapi deploy gelombang ini live; log deploy-log.md; evidence t12 — BUTUH RE-DEPLOY setelah T11 (BUTUH-ACC fresh) |

Gelombang eksekusi:
- G1 (paralel aman, nol irisan): 01, 03, 04, 06, 07
- G2: 02 (butuh 01), 05 (butuh 04), 08 (butuh 01), 09 (butuh 07)
- G3: 10 (butuh 01,04,06,07)
- G4: 11 (butuh G2 + sesi sebelah KELAR) → 12 (BUTUH-ACC)

