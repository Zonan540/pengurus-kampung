# Pengurus Kampung

Game pengurusan bola sepak berasaskan teks dengan kelab daerah Malaysia rekaan, oleh The Blue Podcast Malaysia.
Game ini berjalan sepenuhnya dalam pelayar tanpa backend, dan dihoskan di Netlify (https://pengurus-kampung.netlify.app).

## Struktur

| Folder / fail | Isi |
| --- | --- |
| `site/` | Semua fail yang di-deploy ke Netlify. Folder ini yang diseret ke tab Deploys. |
| `site/index.html` | Seluruh game: CSS, pintu beta dan telemetri, serta skrip utama. |
| `site/vendor/` | `lz-string` (simpanan lama dan eksport) dan `fflate` (format simpanan F, 2.0). |
| `site/sw.js` | Service worker untuk main luar talian. Tukar `CACHE` setiap keluaran. |
| `site/nota.html` | Nota versi awam dan isu diketahui. |
| `site/beta.json` | Suis `closed` untuk pendaftaran beta, serta senarai kod disekat. |
| `site/netlify.toml` | Header cache. |
| `tests/` | Ujian Playwright (lihat bawah). |

## Nombor versi

Ada tiga nombor yang mesti ditukar serentak setiap keluaran:

1. `VERSION` dalam `site/index.html`, iaitu label awam, contohnya `Versi 1.4.3.3`.
2. `BUILD` dalam `site/index.html`, iaitu nombor dalaman, contohnya `b1463`.
3. `CACHE` dalam `site/sw.js`, contohnya `pk-1-4-6-3`.

Tambah juga entri dalam `site/nota.html`.

| Dalaman | Awam |
| --- | --- |
| 1.4.6.2 | Versi 1.4.3.2 |
| 1.4.6.3 | Versi 1.4.3.3 |
| 1.4.6.4 | Versi 1.4.3.4 |
| 1.4.6.5 | Versi 1.4.3.5 |
| 2.0 Beta 6 (`b2006`, `pk-2-0-b6`) | Versi 2.0 Beta 6 |
| 2.1 Beta 1 (`b2101`, `pk-2-1-b1`, SCHEMA 8) | Versi 2.1 Beta 1 |

Cawangan `fasa-8-beta` ialah garis 2.x (SCHEMA 8 mulai 2.1 Beta 1). `main` masih garis 1.x (SCHEMA 1) dan tidak boleh membaca simpanan 2.0, jadi jangan deploy zip daripada `main` ke tapak yang sudah menjalankan 2.0.

## Deploy

1. Semak status `site/beta.json`: `closed: false` (beta dibuka) atau `closed: true` (beta ditutup).
2. Seret folder `site/` ke tab **Deploys** di Netlify. Setiap deploy menggunakan 15 kredit.
3. Jangan sambungkan Netlify kepada GitHub untuk deploy automatik buat masa ini, kerana setiap commit akan menggunakan kredit.

## Ujian

Ujian perlukan Python dan Playwright dengan Chromium.

```
python3 tests/test_musim.py 4        # main 4 musim automatik, semak invarian data, saiz dan masa simpanan
python3 tests/test_simpanan.py 1     # masa simpanan, XSS, storan penuh (hujah = darab perlahan CPU, contohnya 4)
python3 tests/test_inbox_mobile.py   # inbox di telefon dan desktop
python3 tests/test_simpanan_1464.py  # format simpanan, import/eksport, kuota penuh (perlu sejarah git: `git fetch --depth=200 origin main`)
python3 tests/test_fasa2.py          # 2.0 Fasa 2: format simpanan F, save ditangguh, migrasi SCHEMA 2, sandaran pra-2.0
python3 tests/test_fasa3.py          # 2.0 Fasa 3: DOB/umur, sejarah kerjaya, pemain bersara, kecederaan, Medical, RST, rehat, migrasi v3
python3 tests/test_fasa4.py          # 2.0 Fasa 4: kalendar piala, TBPM knockout, Sumbangsih, warna, label jadual, stadium berperingkat, ekonomi AI, migrasi v4
python3 tests/test_fasa5.py          # 2.0 Fasa 5: kelayakan Asia, jadual fasa liga, kalah mati, Piala Super, kalendar, kelab asing, rehat antarabangsa, migrasi v5
python3 tests/test_taktik21.py       # 2.1: formasi tambahan, peranan pemain, keakraban taktik, migrasi v8, simpanan pergi-balik
python3 tests/test_goatcounter.py    # GoatCounter: skrip dimuat, event pintu/sertai/penuh/musim, peranti pemilik dilangkau
python3 tests/baseline_econ.py 12 econ.json  # garis dasar ekonomi 12 musim (median baki, kelab negatif, kapasiti)
python3 tests/baseline_j3.py 6 j3.json   # garis dasar enjin perlawanan (J3)
python3 tests/baseline_econ.py 14 econ.json  # garis dasar ekonomi (I), AI penuh
```

Laporan audit penuh (28 Okt 2026) ada dalam Claude Docs "Audit Kod Pengurus Kampung".
