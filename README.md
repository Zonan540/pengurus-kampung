# Pengurus Kampung

Game pengurusan bola sepak berasaskan teks dengan kelab daerah Malaysia rekaan, oleh The Blue Podcast Malaysia.
Game ini berjalan sepenuhnya dalam pelayar tanpa backend, dan dihoskan di Netlify (https://pengurus-kampung.netlify.app).

## Struktur

| Folder / fail | Isi |
| --- | --- |
| `site/` | Semua fail yang di-deploy ke Netlify. Folder ini yang diseret ke tab Deploys. |
| `site/index.html` | Seluruh game: CSS, pintu beta dan telemetri, serta skrip utama. |
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
```

Laporan audit penuh (28 Okt 2026) ada dalam Claude Docs "Audit Kod Pengurus Kampung".
