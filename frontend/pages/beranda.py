"""
pages/beranda.py
================
Halaman utama (Beranda) — Dashboard "Precision Farming" Kota Pariaman.
"""

import streamlit as st
from db import load_fact_table
from utils import tambah_status_defisiensi

# Ambil informasi pengguna aktif dari session state
user_fullname = st.session_state.get("user_fullname", "Tamu")
user_role = st.session_state.get("role", "Public")

st.title("🌱 Precision Farming Dashboard")
st.subheader("Dinas Pertanian — Kota Pariaman")

st.markdown(f"Selamat datang kembali, **{user_fullname}**!")

# Tampilkan petunjuk khusus berdasarkan peran pengguna
if user_role == "Pimpinan":
    st.markdown(
        """
        Sebagai **Pimpinan (Kepala Dinas / Kepala Bidang)**, Anda memiliki akses penuh ke menu analisis strategis:
        
        *   **📊 Laporan Makro Lahan:** Halaman ini menampilkan peta interaktif sebaran defisiensi hara, tren iklim kuartalan, dan akumulasi kebutuhan pupuk bersubsidi per kecamatan untuk membantu Anda mengambil keputusan alokasi logistik pupuk dan intervensi penyuluhan.
        
        *Silakan gunakan menu di sidebar sebelah kiri untuk meninjau laporan.*
        """
    )
elif user_role == "PPL":
    st.markdown(
        """
        Sebagai **Penyuluh Pertanian Lapangan (PPL)**, Anda dibekali instrumen praktis untuk mendampingi petani:
        
        *   **🌾 Panduan Penyuluh (PPL):** Gunakan kalkulator ini di lapangan. Masukkan data hasil pengukuran kondisi lahan (suhu, kelembapan, N, P, K) untuk mendapatkan rekomendasi instan jenis tanaman yang cocok dibudidayakan serta jenis pupuk pelengkap yang disarankan secara ilmiah.
        
        *Silakan gunakan menu di sidebar sebelah kiri untuk membuka kalkulator.*
        """
    )
elif user_role == "Admin":
    st.markdown(
        """
        Sebagai **Administrator Sistem**, Anda memiliki otorisasi penuh untuk mengelola aplikasi dan data:
        
        *   **📊 Laporan Makro Lahan:** Memantau peta sebaran kesuburan tanah skala kota dan tren kuartalan.
        *   **🌾 Panduan Penyuluh (PPL):** Menggunakan alat bantu kalkulasi preskriptif hara tanah.
        *   **⚙️ Kelola Data:** Mengunggah data hasil pengujian tanah baru (format CSV) untuk memperbarui datamart PostgreSQL secara berkala tanpa merusak star schema yang sudah ada.
        
        *Pilih halaman yang ingin dituju pada menu navigasi di sebelah kiri.*
        """
    )

st.divider()

# Tampilkan ringkasan koneksi datamart agar pengguna tahu statusnya
try:
    df = load_fact_table()
    df = tambah_status_defisiensi(df)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Data Sampel", f"{len(df):,}")
    col2.metric("Jumlah Kecamatan", df["Kecamatan"].nunique())
    col3.metric("Rentang Data", f"{df['Tanggal_Uji'].min().date()} → {df['Tanggal_Uji'].max().date()}")
    pct_kritis = (df["Status_Defisiensi_Hara"] == "Kritis").mean() * 100
    col4.metric("Lahan Kategori Kritis", f"{pct_kritis:.1f}%")

    st.success("✅ Koneksi ke datamart PostgreSQL berhasil terhubung.")
except Exception as e:
    st.error(
        "❌ Gagal terhubung ke datamart PostgreSQL. "
        "Pastikan database sudah berjalan dan kredensial pada "
        "`.streamlit/secrets.toml` sudah benar."
    )
    st.exception(e)
