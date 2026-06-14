# Dashboard Streamlit

Aplikasi dashboard berbasis Streamlit untuk menyajikan analisis tanah dan rekomendasi pemupukan secara interaktif di Kota Pariaman. Data dibaca dari datamart PostgreSQL (star schema).

## Hak Akses (Role-Based Access Control)

Sidebar navigasi diatur secara dinamis berdasarkan peran pengguna setelah login:

*   **Pimpinan** (Kredensial: `pimpinan` / `pimpinan123`): Mengakses Laporan Makro Lahan.
*   **Penyuluh (PPL)** (Kredensial: `ppl` / `ppl123`): Mengakses Panduan Penyuluh (PPL).
*   **Admin** (Kredensial: `admin` / `admin123`): Mengakses semua halaman termasuk menu Kelola Data.

## Struktur Folder

```text
frontend/
├── app.py                      # Entrypoint utama, penanganan login, dan navigasi
├── db.py                       # Helper database (caching query & modul import data)
├── utils.py                    # Ambang batas hara & penentuan koordinat kecamatan
├── requirements.txt            # Dependensi python
├── .streamlit/
│   └── secrets.toml.example    # Contoh konfigurasi database
└── pages/
    ├── beranda.py              # Halaman beranda & status koneksi database
    ├── laporan_makro_lahan.py  # Analisis spasial & tren makro (Pimpinan)
    ├── panduan_penyuluh_ppl.py # Kalkulator kesuburan hara berbasis k-NN (PPL)
    └── kelola_data.py          # Upload CSV data baru secara incremental (Admin)
```

## Panduan Menjalankan Aplikasi

1.  **Persiapan Database:** Pastikan skema `precision_farming` di PostgreSQL sudah terbuat lewat notebook ETL.
2.  **Instalasi Library:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Kredensial Database:** Salin template konfigurasi rahasia:
    ```bash
    cp .streamlit/secrets.toml.example .streamlit/secrets.toml
    ```
    Sesuaikan bagian isi file `.streamlit/secrets.toml` dengan konfigurasi PostgreSQL lokal Anda.
4.  **Jalankan Server:**
    ```bash
    streamlit run app.py
    ```
    Aplikasi dapat diakses pada alamat `http://localhost:8501`.

## Penjelasan Teknis Utama

*   **Policy Engine:** Menganalisis tingkat kritis lahan per kecamatan berdasarkan filter pimpinan secara realtime untuk menyarankan jenis alokasi pupuk prioritas.
*   **Kalkulator Rekomendasi Tanam (k-NN):** Mencari 10 titik data historis terdekat berdasarkan kesamaan karakteristik suhu, kelembapan, dan NPK untuk menyarankan kecocokan komoditas serta pupuk tambahan.
*   **Kelola Data:** Menyediakan antarmuka bagi Admin untuk mengimpor data uji tanah baru dari file CSV ke PostgreSQL secara incremental tanpa merusak skema relasional.