# Laporan Fasa 6, 7 dan 8 (Versi 2.0 Beta 1)

## Fasa 6 – Pindahan dan moral (branch fasa-6-pindah)
Had pinjaman 3 masuk/3 keluar semusim, keputusan pemain (terima/tolak tawaran), tawaran tamat tempoh (6 hari), hari akhir pindahan, interaksi pemain, piramid moral skuad, scouting dengan pengintip (min 3). 17 semakan automatik lulus.

## Fasa 7 – Pencapaian dan sambutan (branch fasa-7-main)
13 pencapaian, giliran sambutan, 8 tahap reputasi, Pasukan Terbaik Musim (ABK, seret-lepas), skrin proses 1.2s pada minggu perlawanan, audit enjin J3 (enjin seimbang, tiada perubahan; keletihan kesan terbesar).

## Fasa 8 – Penerimaan (branch fasa-8-beta)
- Ujian jangka panjang `tests/test_jangka_panjang.py`: 15 musim, 0 ralat konsol, 0 pelanggaran invariant, bulatan simpan (utf16/b64) sama.
- Saiz simpanan terpadat: ~607 KB selepas 15 musim (~23 KB/musim; anggaran 50 musim ~1.7 MB, muat dalam had localStorage).
- Masa pack ~70–110 ms; render <15 ms; semua 28 paparan <10 ms.
- Ekonomi (median baki selepas 15 musim): T1 7.9 juta (tiada negatif), T2 0.6 juta (5/20 negatif), T3 0.55 juta (5/20 negatif). Dianggap munasabah; tiada penalaan.
- Regresi fasa 2–7 dan simpanan 1.4.6.4 lulus. Skema 7; simpanan lama dimigrasi.
- Versi: `Versi 2.0 Beta 1`, build `b2001`, cache SW `pk-2-0-b1`. Nota versi dikemas kini.

## Perkara terbuka (kecil)
- Perlawanan Asia belum masuk senarai penjaring.
- Pemain INT belum disekat daripada Asia.
- `J.gf/ga` hanya dikira dari 2.0.
- Tiada deploy dibuat; `main` tidak disentuh.
