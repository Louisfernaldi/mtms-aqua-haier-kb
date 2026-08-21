# Estafet Fitur Perbandingan Dinamis

| id | tiket | status | dependensi |
|---|---|---|---|
| 01 | Bakukan skema dan migrasi | belum-mulai | - |
| 02 | Bangun API dan editor dinamis | belum-mulai | 01 |
| 03 | Riset spesifikasi semua model | belum-mulai | 01 |
| 04 | Tampilkan perbandingan dan modal | belum-mulai | 02, 03 |
| 05 | Bangun tombol riset ulang | belum-mulai | 02, 03 |
| 06 | Verifikasi dan deploy | belum-mulai | 04, 05 |

Aturan: 02 dan 03 boleh paralel karena file tulisnya dipisah staging; 04 dan 05 mulai setelah keduanya lulus. Tiket 06 berhenti sebelum deploy/tulis data live sampai ACC Louis.
