# Aturan Proyek MTMS AQUA HAIER

- Sumber kebenaran data editable: repo privat `Louisfernaldi/mtms-aqua-haier-kb-data`; data bawaan `site/data` hanya fallback cepat dan artefak deploy.
- Edit user selalu menang atas hasil riset otomatis.
- Setiap nilai hasil riset wajib menyimpan URL sumber dan waktu verifikasi.
- Riset tidak boleh menulis data live tanpa review user.
- Data harga hanya dibaca/ditampilkan; perubahan harga marketplace di luar cakupan.
- Deploy Cloudflare Pages dan tulisan ke repo data live wajib berhenti di gerbang ACC Louis.
- Perubahan UI wajib lulus desktop 1440px dan mobile 390px, nol error console dan nol horizontal overflow.
- Perintah bukti induk: `python -X utf8 tools/verify_product_detail.py`.
