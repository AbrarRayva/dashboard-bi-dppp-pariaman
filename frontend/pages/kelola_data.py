"""
pages/kelola_data.py
====================
Halaman pengelolaan data (Admin Only) — melakukan upload CSV raw secara
incremental untuk memperbarui datamart.
"""

import streamlit as st
import pandas as pd
from db import get_db_stats, ingest_new_csv

# Proteksi halaman dari akses tanpa login / tanpa wewenang Admin
if not st.session_state.get("logged_in", False) or st.session_state.get("role") != "Admin":
    st.error("Akses Ditolak. Halaman ini hanya untuk Administrator Sistem.")
    st.stop()

st.title("⚙️ Kelola Data Pertanian")
st.caption("Pembaruan data secara berkala dan manajemen kapasitas datamart")

# 1. Tampilkan statistik database saat ini
st.markdown("### 📊 Status Datamart Saat Ini")
try:
    stats = get_db_stats()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Sampel Lahan", f"{stats['total_facts']:,}")
    c2.metric("Rentang Pengujian", f"{stats['min_date']} s.d. {stats['max_date']}")
    c3.metric("Kombinasi Tanaman", stats["total_komoditas"])
    c4.metric("Jenis Pupuk Terdaftar", stats["total_pupuk"])
except Exception as e:
    st.error(f"Gagal memuat statistik database: {e}")
    st.stop()

st.divider()

# 2. Upload Data Baru
st.markdown("### 📤 Unggah Data Hasil Uji Tanah Baru")
st.markdown(
    """
    Anda dapat menambahkan data hasil pengujian tanah baru ke database secara berkelanjutan. 
    Sistem akan otomatis mencocokkan data kategori dengan tabel dimensi yang ada, 
    dan membuat entri baru jika ditemukan jenis tanaman, pupuk, atau tanah baru.
    """
)

# Panduan format CSV
with st.expander("Format Kolom CSV yang Diterima (Klik untuk detail)"):
    st.write(
        """
        File CSV harus memiliki kolom-kolom berikut (tidak sensitif terhadap kapitalisasi):
        - **Temperature** (atau *Temparature*) : Suhu udara (°C)
        - **Humidity** : Kelembapan udara (%)
        - **Moisture** : Kelembapan tanah (%)
        - **Soil Type** : Jenis tanah (cth: Sandy, Clayey, Loamy, Red, Black)
        - **Crop Type** : Jenis tanaman (cth: Paddy, Maize, Wheat, dsb)
        - **Nitrogen** : Kandungan Nitrogen tanah
        - **Potassium** : Kandungan Kalium tanah
        - **Phosphorus** (atau *Phosphorous*) : Kandungan Fosfor tanah
        - **Fertilizer Name** : Jenis pupuk yang digunakan (cth: UREA, DAP, dsb)
        
        *Opsional:*
        - **Kecamatan** : Wilayah kecamatan (Pariaman Utara/Tengah/Selatan/Timur). *Jika kosong, sistem akan mengacak kecamatan di Kota Pariaman.*
        - **Tanggal_Uji** : Tanggal pengujian (format YYYY-MM-DD). *Jika kosong, tanggal akan diset pada hari ini.*
        """
    )

uploaded_file = st.file_uploader("Pilih file CSV tanah baru", type=["csv"])

if uploaded_file is not None:
    try:
        # Baca file CSV
        new_data = pd.read_csv(uploaded_file)
        
        st.success("File CSV berhasil dibaca!")
        st.markdown("#### Preview 5 Baris Pertama Data Baru:")
        st.dataframe(new_data.head())
        
        st.info(f"Terdeteksi sebanyak {len(new_data):,} baris data baru yang siap diimpor.")
        
        # Tombol konfirmasi unggah
        if st.button("Simpan & Gabungkan Data ke Datamart", type="primary", use_container_width=True):
            with st.spinner("Sedang memproses dan mengimpor data ke PostgreSQL..."):
                ingest_new_csv(new_data)
            st.success("✅ Sukses! Data baru telah berhasil diimpor dan digabungkan ke datamart.")
            st.balloons()
            
            # Refresh statistik halaman secara manual
            st.rerun()
            
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses data: {e}")
