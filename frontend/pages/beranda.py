"""
pages/beranda.py
================
Halaman utama (Beranda) — Dashboard "Precision Farming" Kota Pariaman.
"""

import streamlit as st
from db import load_fact_table
from utils import tambah_status_defisiensi, tampilkan_kpi_card, suntik_font_inter

# Ambil informasi pengguna aktif dari session state
user_fullname = st.session_state.get("user_fullname", "Tamu")
user_role = st.session_state.get("role", "Public")

suntik_font_inter()

st.title("Precision Farming Dashboard")
st.caption("Dinas Pertanian Kota Pariaman")
st.write("")

# Tampilkan informasi portal selamat datang dalam container bersih
with st.container(border=True):
    st.markdown(f"### Selamat Datang Kembali, {user_fullname}")
    st.markdown(f"Masuk sebagai: **{user_role}**")
    st.write("")
    
    # Tampilkan petunjuk khusus berdasarkan peran pengguna tanpa emoji
    if user_role == "Pimpinan":
        st.markdown(
            """
            Sebagai **Pimpinan (Kepala Dinas / Kepala Bidang)**, Anda memiliki akses penuh ke menu analisis strategis:
            
            *   **Laporan Makro Lahan:** Halaman ini menampilkan peta interaktif sebaran defisiensi hara, tren iklim kuartalan, dan akumulasi kebutuhan pupuk bersubsidi per kecamatan untuk membantu Anda mengambil keputusan alokasi logistik pupuk dan intervensi penyuluhan.
            
            *Silakan gunakan menu navigasi di sidebar sebelah kiri untuk meninjau laporan.*
            """
        )
    elif user_role == "PPL":
        st.markdown(
            """
            Sebagai **Penyuluh Pertanian Lapangan (PPL)**, Anda dibekali instrumen praktis untuk mendampingi petani:
            
            *   **Panduan Penyuluh (PPL):** Gunakan kalkulator ini di lapangan. Masukkan data hasil pengukuran kondisi lahan (suhu, kelembapan, N, P, K) untuk mendapatkan rekomendasi instan jenis tanaman yang cocok dibudidayakan serta jenis pupuk pelengkap yang disarankan secara ilmiah.
            
            *Silakan gunakan menu navigasi di sidebar sebelah kiri untuk membuka kalkulator.*
            """
        )
    elif user_role == "Admin":
        st.markdown(
            """
            Sebagai **Administrator Sistem**, Anda memiliki otorisasi penuh untuk mengelola aplikasi dan data:
            
            *   **Laporan Makro Lahan:** Memantau peta sebaran kesuburan tanah skala kota dan tren kuartalan.
            *   **Panduan Penyuluh (PPL):** Menggunakan alat bantu kalkulasi preskriptif hara tanah.
            *   **Kelola Data:** Mengunggah data hasil pengujian tanah baru (format CSV) untuk memperbarui datamart PostgreSQL secara berkala tanpa merusak star schema yang sudah ada.
            
            *Pilih halaman yang ingin dituju pada menu navigasi di sebelah kiri.*
            """
        )

st.write("")
st.markdown("### Ringkasan Informasi Datamart")

# Tampilkan ringkasan koneksi datamart agar pengguna tahu statusnya
try:
    df = load_fact_table()
    df = tambah_status_defisiensi(df)

    # Filter Tahun Ringkasan
    tahun_opsi = ["Semua Tahun"] + sorted([int(y) for y in df["Tahun"].unique()])
    tahun_pilih = st.selectbox("Pilih Tahun Ringkasan", tahun_opsi, index=0)

    if tahun_pilih != "Semua Tahun":
        df_filtered = df[df["Tahun"] == tahun_pilih]
    else:
        df_filtered = df

    if df_filtered.empty:
        st.warning("Tidak ada data untuk tahun yang dipilih.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            tampilkan_kpi_card("Total Sampel Lahan", f"{len(df_filtered):,}")
                
        with col2:
            tampilkan_kpi_card("Jumlah Kecamatan", str(df_filtered["Kecamatan"].nunique()))
                
        with col3:
            tampilkan_kpi_card("Rentang Tanggal Pengujian", f"{df_filtered['Tanggal_Uji'].min().date()} s.d. {df_filtered['Tanggal_Uji'].max().date()}")
                
        with col4:
            pct_kritis = (df_filtered["Status_Defisiensi_Hara"] == "Kritis").mean() * 100
            tampilkan_kpi_card("Lahan Kategori Kritis", f"{pct_kritis:.1f}%")

    st.write("")
    st.info("Koneksi ke datamart PostgreSQL berhasil terhubung.")
except Exception as e:
    st.error(
        "Gagal terhubung ke datamart PostgreSQL. "
        "Pastikan database sudah berjalan dan kredensial pada "
        "`.streamlit/secrets.toml` sudah benar."
    )
    st.exception(e)
