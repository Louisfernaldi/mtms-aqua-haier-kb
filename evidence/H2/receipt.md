tiket: H2 (rombak produk: galeri multi-foto + fitur + preview PDF)
status: kelar
model: sesi-utama (mandor benerin tombol Preview file.html + verifikasi ulang)
mulai_wib: ~18:00
selesai_wib: ~19:30
bukti:
  - gen_data_js.py: 37 kartu, 10 multi-foto, 21 dengan fitur
  - verify_file_proto.py: EXIT 0 (errors 0, render_gagal 0)
  - cek_H2_mandor.py: 37 cards, thumbs 6, nav 2, klik thumbnail src berubah (0.jpg->1.jpg), 0 console error
  - cek_H2_fitur.py: h4 'Fitur Unggulan' + ul 6 li (contoh: Twin Inverter)
  - cek_H2_files3.py: file.html 27 li, 8 btn-preview, klik -> overlay+iframe src files/Product%20Knowledge/Aqua%20TV%20one-pager.pdf
  - cek_H2_kompetitor.py: btn 'Unduh PDF' + 'Preview PDF' (btn-sec) + 5 chip, 0 error
