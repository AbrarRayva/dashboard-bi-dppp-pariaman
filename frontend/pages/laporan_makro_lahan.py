"""
pages/laporan_makro_lahan.py
============================
Halaman "Laporan Makro Lahan" — untuk Kepala Dinas & Kepala Bidang.

Komponen:
- KPI Cards
- Analisis Rekomendasi Kebijakan & Rencana Aksi (Actionable Insights)
- Peta sebaran (Heatmap) defisiensi hara per Kecamatan + Penjelasan Geografis
- Line chart Time-Series (tren kuartalan) + Penjelasan Pola Musiman
- Clustered Bar Chart frekuensi rekomendasi pupuk + Analisis Kebutuhan
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from db import load_fact_table
from utils import (
    tambah_status_defisiensi,
    lengkapi_koordinat,
    urutkan_kuartal,
    THRESHOLD_N,
    THRESHOLD_P,
    THRESHOLD_K,
)

st.title("📊 Laporan Makro Lahan")
st.caption("Ringkasan kondisi agrikultur skala makro untuk pengambil keputusan — Dinas Pertanian Kota Pariaman")

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
df = load_fact_table()
df = tambah_status_defisiensi(df)

# ---------------------------------------------------------------------------
# Filter global (sidebar)
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("🔎 Filter Laporan")
    tahun_opsi = sorted(df["Tahun"].unique())
    tahun_pilih = st.multiselect("Tahun Pengujian", tahun_opsi, default=tahun_opsi)

    kecamatan_opsi = sorted(df["Kecamatan"].unique())
    kecamatan_pilih = st.multiselect("Kecamatan", kecamatan_opsi, default=kecamatan_opsi)

df_f = df[df["Tahun"].isin(tahun_pilih) & df["Kecamatan"].isin(kecamatan_pilih)]

if df_f.empty:
    st.warning("Tidak ada data untuk filter yang dipilih. Silakan ubah filter di sidebar.")
    st.stop()

# ---------------------------------------------------------------------------
# KPI CARDS
# ---------------------------------------------------------------------------
st.markdown("### 🧮 KPI Utama Wilayah")

total_sampel = len(df_f)
rata_suhu = df_f["Temperature"].mean()
rata_kelembapan = df_f["Humidity"].mean()

jumlah_kritis_per_kec = (
    df_f[df_f["Status_Defisiensi_Hara"] == "Kritis"]
    .groupby("Kecamatan")
    .size()
    .sort_values(ascending=False)
)
kecamatan_kritis_tertinggi = jumlah_kritis_per_kec.index[0] if len(jumlah_kritis_per_kec) else "-"
jumlah_kritis_tertinggi = jumlah_kritis_per_kec.iloc[0] if len(jumlah_kritis_per_kec) else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Sampel Lahan", f"{total_sampel:,}")
col2.metric("Rata-rata Suhu", f"{rata_suhu:.1f} °C")
col3.metric("Rata-rata Kelembapan", f"{rata_kelembapan:.1f} %")
col4.metric(
    "Kecamatan Paling Kritis",
    kecamatan_kritis_tertinggi,
    help=f"{jumlah_kritis_tertinggi} sampel berstatus 'Kritis'",
)

st.divider()

# ---------------------------------------------------------------------------
# PETA SEBARAN (HEATMAP) DEFISIENSI HARA PER KECAMATAN
# ---------------------------------------------------------------------------
ringkasan_kec = (
    df_f.groupby("Kecamatan")
    .agg(
        rata_n=("Nitrogen", "mean"),
        rata_p=("Phosphorus", "mean"),
        rata_k=("Potassium", "mean"),
        jumlah_sampel=("id_fakta", "count"),
        jumlah_kritis=("Status_Defisiensi_Hara", lambda s: (s == "Kritis").sum()),
    )
    .reset_index()
)
ringkasan_kec["pct_kritis"] = (
    ringkasan_kec["jumlah_kritis"] / ringkasan_kec["jumlah_sampel"] * 100
)
ringkasan_kec = lengkapi_koordinat(ringkasan_kec, "Kecamatan")

# ---------------------------------------------------------------------------
# REKOMENDASI KEBIJAKAN & RENCANA AKSI (ACTIONABLE INSIGHTS)
# ---------------------------------------------------------------------------
st.markdown("### 📋 Rekomendasi Kebijakan & Rencana Aksi Dinas")

if not ringkasan_kec.empty:
    kec_tertinggi_row = ringkasan_kec.loc[ringkasan_kec["pct_kritis"].idxmax()]
    kec_kritis_nama = kec_tertinggi_row["Kecamatan"]
    kec_kritis_pct = kec_tertinggi_row["pct_kritis"]
    
    df_kec_kritis = df_f[df_f["Kecamatan"] == kec_kritis_nama]
    n_kritis_pct = (df_kec_kritis["Nitrogen"] < THRESHOLD_N).mean() * 100
    p_kritis_pct = (df_kec_kritis["Phosphorus"] < THRESHOLD_P).mean() * 100
    k_kritis_pct = (df_kec_kritis["Potassium"] < THRESHOLD_K).mean() * 100
    
    haras = [
        ("Nitrogen (N)", n_kritis_pct, "UREA (untuk menambah unsur Nitrogen)"),
        ("Phosphorus (P)", p_kritis_pct, "DAP / SP-36 (untuk merangsang pertumbuhan akar)"),
        ("Potassium (K)", k_kritis_pct, "KCl / NPK (untuk memperkuat batang & ketahanan penyakit)"),
    ]
    haras_sorted = sorted(haras, key=lambda x: x[1], reverse=True)
    unsur_terkritis, unsur_pct, pupuk_saran = haras_sorted[0]
    
    top_pupuk_kec = (
        df_kec_kritis["Fertilizer_Name"].value_counts().index[0]
        if not df_kec_kritis.empty
        else "UREA"
    )
    
    st.markdown(
        f"""
        Berdasarkan filter data yang Anda pilih, berikut analisis prioritas tindakan yang perlu diambil:
        
        *   **Urgensi Wilayah Utama:** Kecamatan **{kec_kritis_nama}** menuntut prioritas pertama karena **{kec_kritis_pct:.1f}%** dari sampel lahannya masuk dalam kategori **Kritis** (kekurangan satu atau lebih unsur hara utama).
        *   **Identifikasi Masalah Utama:** Unsur hara tanah yang paling tidak terpenuhi di {kec_kritis_nama} adalah **{unsur_terkritis}** (terdapat **{unsur_pct:.1f}%** sampel di bawah ambang batas batas tumbuh optimal).
        
        **Tindakan Kebijakan yang Direkomendasikan:**
        1.  **Distribusi Pupuk Bersubsidi Terfokus:** Segera instruksikan penyaluran prioritas pupuk jenis **{top_pupuk_kec}** dan **{pupuk_saran}** ke wilayah kecamatan **{kec_kritis_nama}** untuk mencegah penurunan produktivitas hasil panen.
        2.  **Sosialisasi Intervensi Lahan:** Tugaskan PPL (Penyuluh Pertanian Lapangan) di kecamatan **{kec_kritis_nama}** untuk mengedukasi kelompok tani agar beralih ke metode pemupukan berimbang khusus guna memulihkan kandungan **{unsur_terkritis}**.
        """
    )
else:
    st.info("Aktifkan filter kecamatan di sidebar untuk menampilkan rekomendasi kebijakan.")

st.divider()

# ---------------------------------------------------------------------------
# RENDERING PETA
# ---------------------------------------------------------------------------
st.markdown("### 🗺️ Peta Sebaran Defisiensi Hara per Kecamatan")

fig_map = px.scatter_map(
    ringkasan_kec,
    lat="lat",
    lon="lon",
    size="jumlah_sampel",
    color="pct_kritis",
    color_continuous_scale="YlOrRd",
    size_max=45,
    zoom=11.5,
    hover_name="Kecamatan",
    hover_data={
        "lat": False,
        "lon": False,
        "pct_kritis": ":.1f",
        "jumlah_sampel": True,
        "rata_n": ":.1f",
        "rata_p": ":.1f",
        "rata_k": ":.1f",
    },
    map_style="open-street-map",
    labels={"pct_kritis": "% Kritis", "jumlah_sampel": "Jumlah Sampel"},
)
fig_map.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=420)
st.plotly_chart(fig_map, width="stretch")

st.markdown(
    """
    **💡 Analisis Geografis Lahan:**
    *   **Asal Data:** Peta sebaran di atas mengagregasikan koordinat administrasi desa pusat aktivitas pertanian di tiap kecamatan. Warna merah yang pekat melambangkan konsentrasi lahan kritis yang tinggi.
    *   **Mengapa Polanya Demikian?** Wilayah pesisir barat seperti *Pariaman Utara* memiliki kontur tanah yang cenderung *Sandy* (berpasir). Tanah berpasir memiliki kapasitas retensi hara yang sangat rendah. Ketika terjadi hujan dengan intensitas sedang hingga tinggi, air dengan cepat melarutkan dan menghanyutkan unsur hara Nitrogen (pencucian/leaching) ke dalam tanah bawah yang tidak terjangkau akar tanaman pendek, menyebabkan angka kritis wilayah pesisir lebih tinggi dibanding wilayah timur yang berjenis tanah lempung.
    """
)

st.divider()

# ---------------------------------------------------------------------------
# LINE CHART - TIME SERIES (TREN KUARTALAN)
# ---------------------------------------------------------------------------
st.markdown("### 📈 Tren Kuartalan Iklim vs Kandungan Tanah")

tren = (
    df_f.groupby(["Tahun", "Kuartal", "Nama_Kuartal"])
    .agg(
        rata_suhu=("Temperature", "mean"),
        rata_kelembapan=("Humidity", "mean"),
        rata_kelembapan_tanah=("Moisture", "mean"),
    )
    .reset_index()
)
tren = urutkan_kuartal(tren)

tren_long = tren.melt(
    id_vars=["Nama_Kuartal", "Tahun", "Kuartal"],
    value_vars=["rata_suhu", "rata_kelembapan", "rata_kelembapan_tanah"],
    var_name="Metrik",
    value_name="Nilai",
)
nama_metrik = {
    "rata_suhu": "Rata-rata Suhu (°C)",
    "rata_kelembapan": "Rata-rata Kelembapan Udara (%)",
    "rata_kelembapan_tanah": "Rata-rata Kelembapan Tanah (%)",
}
tren_long["Metrik"] = tren_long["Metrik"].map(nama_metrik)

fig_line = px.line(
    tren_long,
    x="Nama_Kuartal",
    y="Nilai",
    color="Metrik",
    markers=True,
)
fig_line.update_layout(
    xaxis_title="Kuartal",
    yaxis_title="Nilai Rata-rata",
    legend_title=None,
    height=420,
)
st.plotly_chart(fig_line, width="stretch")

st.markdown(
    """
    **💡 Analisis Tren Iklim Musiman:**
    *   **Asal Data:** Grafik tren runtun waktu ini dibuat menggunakan rata-rata berkala dari data pengujian laboratorium Dinas Pertanian sepanjang 2023 hingga 2026.
    *   **Mengapa Polanya Demikian?** Kandungan kelembapan tanah (*Moisture*) mengikuti siklus curah hujan lokal Sumatera Barat secara musiman. Terlihat fluktuasi kelembapan tanah di mana kelembapan melonjak pada Q1/Q4 (musim penghujan) dan turun pada Q2/Q3 (musim kemarau). Menariknya, pada kuartal pasca-panen raya, kelembapan tanah yang tinggi mempercepat proses mineralisasi organik, namun jika diikuti hujan lebat, unsur hara larut air akan ikut terbilas. Hal ini menerangkan mengapa pasca Q2 dan Q4 sering terjadi penurunan kualitas kesuburan lahan secara signifikan jika tidak segera diimbangi pemupukan dasar.
    """
)

st.divider()

# ---------------------------------------------------------------------------
# CLUSTERED BAR CHART - FREKUENSI REKOMENDASI PUPUK PER KECAMATAN
# ---------------------------------------------------------------------------
st.markdown("### 🌾 Akumulasi Kebutuhan Jenis Pupuk Bersubsidi")

pupuk_kec = (
    df_f.groupby(["Kecamatan", "Fertilizer_Name"])
    .size()
    .reset_index(name="Total_Rekomendasi")
)

fig_bar = px.bar(
    pupuk_kec,
    x="Kecamatan",
    y="Total_Rekomendasi",
    color="Fertilizer_Name",
    barmode="group",
    labels={"Fertilizer_Name": "Jenis Pupuk", "Total_Rekomendasi": "Total Rekomendasi"},
)
fig_bar.update_layout(height=450, legend_title="Jenis Pupuk")
st.plotly_chart(fig_bar, width="stretch")

st.markdown(
    """
    **💡 Analisis Kebutuhan Pupuk & Logistik:**
    *   **Asal Data:** Grafik batang klaster ini dihitung dari pencocokan riwayat kesuksesan kombinasi pemupukan dari data mart, dikelompokkan berdasarkan batas wilayah kecamatan.
    *   **Mengapa Polanya Demikian?** Jenis pupuk **UREA** mendominasi rekomendasi di hampir seluruh kecamatan karena UREA merupakan sumber Nitrogen tunggal paling efektif untuk fase vegetatif awal tanaman pangan. Pada kecamatan yang didominasi tanah lempung seperti *Pariaman Timur*, terlihat kebutuhan akan **NPK** (seperti *10-26-26* atau *17-17-17*) lebih bervariasi karena komoditas yang ditanam di sana mencakup buah-buahan dan sayuran (hortikultura) yang membutuhkan nutrisi Fosfor dan Kalium seimbang untuk merangsang fase pembuahan, berbeda dengan padi sawah yang cenderung membutuhkan suplai pupuk Nitrogen/Urea masif.
    """
)
