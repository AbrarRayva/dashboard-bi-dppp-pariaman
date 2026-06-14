# Dashboard Business Intelligence (BI) DPPP Kota Pariaman

Sistem analisis kesuburan tanah dan rekomendasi pemupukan (precision farming) untuk Dinas Pertanian, Pangan dan Perikanan Kota Pariaman. Terdiri dari modul ETL data dan dashboard visualisasi.

## Struktur Repositori

*   frontend/ - Aplikasi dashboard visualisasi (Streamlit)
*   notebook/ - Notebook ETL untuk pengolahan data mentah ke PostgreSQL
*   raw-dataset-csv/ - Dataset mentah awal
*   star-schema-csv/ - Backup ekspor data hasil ETL

## Alur Dijalankan

1.  **Tahap 1 (ETL):** Dijalankan melalui `notebook/etl-preprocessing.ipynb` untuk memproses data mentah dan memuatnya ke database PostgreSQL skema `precision_farming`.
2.  **Tahap 2 (Dashboard):** Dijalankan melalui direktori `frontend/` untuk menyajikan visualisasi data kesuburan tanah kepada pimpinan dan penyuluh lapangan. Petunjuk detail berada di [frontend/README.md](frontend/README.md).

## Anggota Kelompok
*   Siti Aliani Husnah.F (2311522006)
*   Muhammad Abrar Rayva (2311522012)