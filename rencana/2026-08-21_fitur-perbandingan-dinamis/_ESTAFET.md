# Estafet Fitur Perbandingan Dinamis

| id | tiket | status | dependensi |
|---|---|---|---|
| 01 | Bakukan skema dan migrasi | kelar-live | - |
| 02 | Bangun API dan editor dinamis | kelar-live | 01 |
| 03 | Riset spesifikasi semua model | kelar | 01 |
| 04 | Tampilkan perbandingan dan modal | kelar-live | 02, 03 |
| 05 | Bangun tombol riset ulang | kelar-live | 02, 03 |
| 06 | Verifikasi dan deploy | kelar-live | 04, 05 |

Aturan: 02 dan 03 boleh paralel karena file tulisnya dipisah staging; 04 dan 05 mulai setelah keduanya lulus. Tiket 06 berhenti sebelum deploy/tulis data live sampai ACC Louis.
