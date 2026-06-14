"""
pages/laporan_makro_lahan.py
============================
Halaman "Laporan Makro Lahan" — untuk Kepala Dinas & Kepala Bidang.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from db import load_fact_table
from utils import (
    tambah_status_defisiensi,
    lengkapi_koordinat,
    urutkan_kuartal,
    THRESHOLD_N,
    THRESHOLD_P,
    THRESHOLD_K,
    tampilkan_kpi_card,
    suntik_font_inter,
)

suntik_font_inter()

st.title("Laporan Makro Lahan")
st.caption("Ringkasan kondisi agrikultur skala makro untuk pengambil keputusan — Dinas Pertanian Kota Pariaman")
st.write("")

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
df = load_fact_table()
df = tambah_status_defisiensi(df)

# ---------------------------------------------------------------------------
# Filter global (sidebar) - Dinamis & Interaktif
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Filter Laporan")
    
    tahun_opsi = sorted(df["Tahun"].unique())
    tahun_pilih = st.multiselect("Tahun Pengujian", tahun_opsi, default=tahun_opsi)

    kecamatan_opsi = sorted(df["Kecamatan"].unique())
    kecamatan_pilih = st.multiselect("Kecamatan", kecamatan_opsi, default=kecamatan_opsi)

    komoditas_opsi = sorted(df["Crop_Type"].unique())
    komoditas_pilih = st.multiselect("Komoditas (Crop Type)", komoditas_opsi, default=komoditas_opsi)

    pupuk_opsi = sorted(df["Fertilizer_Name"].unique())
    pupuk_pilih = st.multiselect("Jenis Pupuk Utama", pupuk_opsi, default=pupuk_opsi)

    tanah_opsi = sorted(df["Jenis_Tanah"].unique())
    tanah_pilih = st.multiselect("Jenis Tanah Lahan", tanah_opsi, default=tanah_opsi)

# Terapkan filter multiselect secara dinamis
df_f = df[
    df["Tahun"].isin(tahun_pilih) & 
    df["Kecamatan"].isin(kecamatan_pilih) &
    df["Crop_Type"].isin(komoditas_pilih) &
    df["Fertilizer_Name"].isin(pupuk_pilih) &
    df["Jenis_Tanah"].isin(tanah_pilih)
]

if df_f.empty:
    st.warning("Tidak ada data untuk filter yang dipilih. Silakan ubah filter di sidebar.")
    st.stop()

# ---------------------------------------------------------------------------
# AGREGASI DATA KECAMATAN (dihitung awal untuk sinkronisasi KPI & Peringatan)
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

if not ringkasan_kec.empty:
    kec_tertinggi_row = ringkasan_kec.loc[ringkasan_kec["pct_kritis"].idxmax()]
    kec_kritis_nama = kec_tertinggi_row["Kecamatan"]
    kec_kritis_pct = kec_tertinggi_row["pct_kritis"]
    jumlah_kritis_tertinggi = kec_tertinggi_row["jumlah_kritis"]
else:
    kec_kritis_nama = "-"
    kec_kritis_pct = 0.0
    jumlah_kritis_tertinggi = 0

# ---------------------------------------------------------------------------
# KPI CARDS
# ---------------------------------------------------------------------------
st.markdown("### KPI Utama Wilayah")

total_sampel = len(df_f)
rata_suhu = df_f["Temperature"].mean()
rata_kelembapan = df_f["Humidity"].mean()

col1, col2, col3, col4 = st.columns(4)

with col1:
    tampilkan_kpi_card("Total Sampel Lahan", f"{total_sampel:,}")
with col2:
    tampilkan_kpi_card("Rata-rata Suhu Lahan", f"{rata_suhu:.1f} °C")
with col3:
    tampilkan_kpi_card("Rata-rata Kelembapan", f"{rata_kelembapan:.1f} %")
with col4:
    tampilkan_kpi_card(
        "Kecamatan Paling Kritis",
        kec_kritis_nama,
        f"{kec_kritis_pct:.1f}% lahan kritis ({jumlah_kritis_tertinggi} sampel)"
    )

st.write("")

# ---------------------------------------------------------------------------
# ALERT & INITIAL RECOMMENDATION PANEL
# ---------------------------------------------------------------------------
if not ringkasan_kec.empty:
    df_kec_kritis = df_f[df_f["Kecamatan"] == kec_kritis_nama]
    n_kritis_pct = (df_kec_kritis["Nitrogen"] < THRESHOLD_N).mean() * 100
    p_kritis_pct = (df_kec_kritis["Phosphorus"] < THRESHOLD_P).mean() * 100
    k_kritis_pct = (df_kec_kritis["Potassium"] < THRESHOLD_K).mean() * 100
    
    haras = [
        ("Nitrogen", n_kritis_pct, "UREA (penambah unsur Nitrogen)"),
        ("Fosfor", p_kritis_pct, "DAP / SP-36 (merangsang pertumbuhan akar)"),
        ("Kalium", k_kritis_pct, "KCl / NPK (memperkuat batang & imunitas)"),
    ]
    haras_sorted = sorted(haras, key=lambda x: x[1], reverse=True)
    unsur_terkritis, unsur_pct, pupuk_saran = haras_sorted[0]
    
    top_pupuk_kec = (
        df_kec_kritis["Fertilizer_Name"].value_counts().index[0]
        if not df_kec_kritis.empty
        else "UREA"
    )
    
    # Render actionable boxes side by side
    act_col1, act_col2 = st.columns(2)
    
    with act_col1:
        st.markdown(
            f"""
            <div style="background-color: #FEF2F2; border-left: 4px solid #EF4444; padding: 16px; border-radius: 4px; height: 100%; font-family: 'Inter', sans-serif;">
                <h4 style="color: #991B1B; margin: 0 0 8px 0; font-family: 'Inter', sans-serif; font-weight: 700;">Peringatan Defisiensi Hara Tinggi</h4>
                <p style="color: #7F1D1D; margin: 0; font-size: 0.95em; line-height: 1.5; font-family: 'Inter', sans-serif;">
                    Kecamatan <b>{kec_kritis_nama}</b> memerlukan intervensi segera. 
                    Sebanyak <b>{kec_kritis_pct:.1f}%</b> sampel lahan di wilayah ini dikategorikan kritis. 
                    Masalah utama didominasi defisit hara <b>{unsur_terkritis}</b> dengan <b>{unsur_pct:.1f}%</b> sampel di bawah batas aman tumbuh optimal.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    with act_col2:
        st.markdown(
            f"""
            <div style="background-color: #F0FDF4; border-left: 4px solid #10B981; padding: 16px; border-radius: 4px; height: 100%; font-family: 'Inter', sans-serif;">
                <h4 style="color: #065F46; margin: 0 0 8px 0; font-family: 'Inter', sans-serif; font-weight: 700;">Rekomendasi Rencana Tindakan</h4>
                <ul style="color: #064E3B; margin: 0; padding-left: 20px; font-size: 0.95em; line-height: 1.5; font-family: 'Inter', sans-serif;">
                    <li><b>Prioritas Distribusi:</b> Salurkan logistik pupuk bersubsidi jenis <b>{top_pupuk_kec}</b> dan <b>{pupuk_saran}</b> ke Kecamatan {kec_kritis_nama} sesegera mungkin.</li>
                    <li><b>Instruksi Lapangan:</b> Tugaskan PPL wilayah {kec_kritis_nama} untuk menyosialisasikan pemupukan berimbang hara {unsur_terkritis} kepada kelompok tani binaan.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )
else:
    st.info("Aktifkan filter kecamatan di sidebar untuk menampilkan analisis rekomendasi tindakan.")

st.write("")
st.divider()

# ---------------------------------------------------------------------------
# CHART 1: PETA SEBARAN DENGAN METRIK DINAMIS (PILIH METRIK)
# ---------------------------------------------------------------------------
st.markdown("### Peta Sebaran Kondisi Lahan per Kecamatan")
st.caption("Pimpinan dapat memodifikasi metrik warna peta untuk menganalisis unsur hara tertentu secara spesifik:")

# Radio button interaktif untuk mengubah metrik peta
map_metric = st.radio(
    "Metrik Peta Sebaran Lahan",
    ["% Lahan Kritis", "Rata-rata Nitrogen (N)", "Rata-rata Fosfor (P)", "Rata-rata Kalium (K)"],
    horizontal=True
)

metric_col = "pct_kritis"
color_scale = "YlOrRd"
metric_label = "% Kritis"
if map_metric == "Rata-rata Nitrogen (N)":
    metric_col = "rata_n"
    color_scale = "RdYlGn"
    metric_label = "Rata-rata Nitrogen"
elif map_metric == "Rata-rata Fosfor (P)":
    metric_col = "rata_p"
    color_scale = "RdYlGn"
    metric_label = "Rata-rata Fosfor"
elif map_metric == "Rata-rata Kalium (K)":
    metric_col = "rata_k"
    color_scale = "RdYlGn"
    metric_label = "Rata-rata Kalium"

fig_map = px.scatter_map(
    ringkasan_kec,
    lat="lat",
    lon="lon",
    size="jumlah_sampel",
    color=metric_col,
    color_continuous_scale=color_scale,
    size_max=45,
    zoom=11.5,
    hover_name="Kecamatan",
    hover_data={
        "lat": False,
        "lon": False,
        "jumlah_sampel": True,
        "pct_kritis": ":.1f",
        "rata_n": ":.1f",
        "rata_p": ":.1f",
        "rata_k": ":.1f",
    },
    map_style="open-street-map",
    labels={metric_col: metric_label, "jumlah_sampel": "Jumlah Sampel"},
)
fig_map.update_layout(
    font=dict(family="Inter"),
    margin=dict(l=0, r=0, t=0, b=0), 
    height=420
)
st.plotly_chart(fig_map, use_container_width=True)

st.markdown(
    """
    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 16px; border-radius: 8px; margin-top: 10px; font-family: 'Inter', sans-serif;">
        <h5 style="color: #334155; margin-top: 0; font-family: 'Inter', sans-serif; font-weight: 700;">Analisis Geografis Lahan</h5>
        <p style="color: #475569; font-size: 0.9em; margin-bottom: 8px; line-height: 1.45; font-family: 'Inter', sans-serif;">
            <b>Asal Data:</b> Peta sebaran di atas mengagregasikan koordinat administrasi desa pusat aktivitas pertanian di tiap kecamatan. Ukuran lingkaran menunjukkan volume sampel pengujian.
        </p>
        <p style="color: #475569; font-size: 0.9em; margin-bottom: 0; line-height: 1.45; font-family: 'Inter', sans-serif;">
            <b>Penyebab Pola Data:</b> Wilayah pesisir barat seperti <i>Pariaman Utara</i> memiliki kontur tanah yang cenderung berpasir (Sandy). Tanah berpasir memiliki kapasitas retensi hara yang sangat rendah. Ketika terjadi hujan dengan intensitas sedang hingga tinggi, air dengan cepat melarutkan dan menghanyutkan unsur hara Nitrogen (pencucian/leaching) ke dalam tanah bawah yang tidak terjangkau akar tanaman pendek, menyebabkan angka kritis wilayah pesisir lebih tinggi dibanding wilayah timur yang berjenis tanah lempung.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.write("")
st.divider()

# ---------------------------------------------------------------------------
# ROW 4: CHART 2 (LINE CHART TIME-SERIES) & CHART 3 (DONUT CHART KESIAPAN)
# ---------------------------------------------------------------------------
chart_col1, chart_col2 = st.columns([2, 1])

with chart_col1:
    st.markdown("### Tren Kuartalan Iklim vs Kandungan Tanah")
    
    mapping_metrik = {
        "Rata-rata Suhu Lahan (°C)": "Temperature",
        "Rata-rata Kelembapan Udara (%)": "Humidity",
        "Rata-rata Kelembapan Tanah (%)": "Moisture",
        "Rata-rata Nitrogen (N)": "Nitrogen",
        "Rata-rata Fosfor (P)": "Phosphorus",
        "Rata-rata Kalium (K)": "Potassium"
    }
    
    metrik_tren_pilih = st.multiselect(
        "Pilih Parameter Tren",
        options=list(mapping_metrik.keys()),
        default=[
            "Rata-rata Suhu Lahan (°C)",
            "Rata-rata Kelembapan Udara (%)",
            "Rata-rata Kelembapan Tanah (%)"
        ]
    )
    
    if not metrik_tren_pilih:
        st.warning("Pilih minimal satu metrik untuk menampilkan grafik tren.")
    else:
        # Menghitung agregasi dinamis berdasarkan pilihan
        tren = (
            df_f.groupby(["Tahun", "Kuartal", "Nama_Kuartal"])
            .agg(**{f"val_{mapping_metrik[m]}": (mapping_metrik[m], "mean") for m in metrik_tren_pilih})
            .reset_index()
        )
        tren = urutkan_kuartal(tren)

        tren_long = tren.melt(
            id_vars=["Nama_Kuartal", "Tahun", "Kuartal"],
            value_vars=[f"val_{mapping_metrik[m]}" for m in metrik_tren_pilih],
            var_name="Metrik",
            value_name="Nilai",
        )
        
        reverse_mapping = {f"val_{mapping_metrik[m]}": m for m in metrik_tren_pilih}
        tren_long["Metrik"] = tren_long["Metrik"].map(reverse_mapping)

        fig_line = px.line(
            tren_long,
            x="Nama_Kuartal",
            y="Nilai",
            color="Metrik",
            markers=True,
        )
        fig_line.update_layout(
            font=dict(family="Inter"),
            xaxis_title="Kuartal",
            yaxis_title="Nilai Rata-rata",
            legend_title=None,
            height=340,
        )
        st.plotly_chart(fig_line, use_container_width=True)

with chart_col2:
    st.markdown("### Status Kesiapan Lahan")
    
    basis_analisis = st.selectbox(
        "Tinjau Status Lahan Berdasarkan",
        [
            "Defisiensi Keseluruhan (N/P/K)", 
            "Kecukupan Nitrogen (N)", 
            "Kecukupan Fosfor (P)", 
            "Kecukupan Kalium (K)"
        ]
    )
    
    # Kalkulasi kategori dinamis berdasarkan pilihan
    df_temp = df_f.copy()
    if basis_analisis == "Kecukupan Nitrogen (N)":
        df_temp["Status_Pie"] = df_temp["Nitrogen"].apply(lambda x: "Aman Tanam" if x >= THRESHOLD_N else "Defisit N")
        color_map = {"Aman Tanam": "#15803d", "Defisit N": "#b91c1c"}
    elif basis_analisis == "Kecukupan Fosfor (P)":
        df_temp["Status_Pie"] = df_temp["Phosphorus"].apply(lambda x: "Aman Tanam" if x >= THRESHOLD_P else "Defisit P")
        color_map = {"Aman Tanam": "#15803d", "Defisit P": "#b91c1c"}
    elif basis_analisis == "Kecukupan Kalium (K)":
        df_temp["Status_Pie"] = df_temp["Potassium"].apply(lambda x: "Aman Tanam" if x >= THRESHOLD_K else "Defisit K")
        color_map = {"Aman Tanam": "#15803d", "Defisit K": "#b91c1c"}
    else:
        df_temp["Status_Pie"] = df_temp["Status_Defisiensi_Hara"].map({"Aman": "Aman Tanam", "Kritis": "Perlu Tindakan"})
        color_map = {"Aman Tanam": "#15803d", "Perlu Tindakan": "#b91c1c"}
        
    status_counts = df_temp["Status_Pie"].value_counts().reset_index()
    status_counts.columns = ["Status Lahan", "Jumlah"]
    
    fig_donut = px.pie(
        status_counts,
        names="Status Lahan",
        values="Jumlah",
        hole=0.4,
        color="Status Lahan",
        color_discrete_map=color_map
    )
    fig_donut.update_layout(
        font=dict(family="Inter"),
        height=340,
        margin=dict(l=20, r=20, t=10, b=20),
        legend_title=None
    )
    st.plotly_chart(fig_donut, use_container_width=True)

st.markdown(
    """
    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 16px; border-radius: 8px; font-family: 'Inter', sans-serif;">
        <h5 style="color: #334155; margin-top: 0; font-family: 'Inter', sans-serif; font-weight: 700;">Analisis Tren Iklim & Kesiapan Lahan</h5>
        <p style="color: #475569; font-size: 0.9em; margin-bottom: 8px; line-height: 1.45; font-family: 'Inter', sans-serif;">
            <b>Asal Data:</b> Grafik tren runtun waktu dan proporsi kesiapan dihitung menggunakan rata-rata berkala dari data pengujian laboratorium Dinas Pertanian sepanjang 2023 hingga 2026.
        </p>
        <p style="color: #475569; font-size: 0.9em; margin-bottom: 0; line-height: 1.45; font-family: 'Inter', sans-serif;">
            <b>Penyebab Pola Data:</b> Kandungan kelembapan tanah (Moisture) mengikuti siklus curah hujan lokal Sumatera Barat secara musiman. Kelembapan melonjak pada Q1/Q4 (musim penghujan) dan turun pada Q2/Q3 (musim kemarau). Pasca-panen raya, kelembapan yang tinggi mempercepat proses mineralisasi organik, namun pencucian hara oleh hujan lebat dapat membilas zat hara larut air. Hal ini menerangkan mengapa penurunan kualitas kesuburan lahan secara signifikan sering terjadi pasca kuartal basah.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.write("")
st.divider()

# ---------------------------------------------------------------------------
# ROW 5: CHART 4 (GROUPED BAR NPK) & CHART 5 (GROUPED BAR FERTILIZER)
# ---------------------------------------------------------------------------
bar_col1, bar_col2 = st.columns(2)

with bar_col1:
    st.markdown("### Perbandingan Kandungan Hara Lahan")
    
    x_axis_mapping = {
        "Kecamatan": "Kecamatan",
        "Jenis Tanah": "Jenis_Tanah",
        "Komoditas": "Crop_Type"
    }
    
    col_x_npk = st.radio(
        "Kelompokkan Sumbu X (Hara)",
        options=list(x_axis_mapping.keys()),
        horizontal=True,
        key="col_x_npk"
    )
    x_col_npk = x_axis_mapping[col_x_npk]
    
    hara_pilih = st.multiselect(
        "Pilih Unsur Hara untuk Dikomparasi",
        options=["Nitrogen", "Phosphorus", "Potassium"],
        default=["Nitrogen", "Phosphorus", "Potassium"],
        key="hara_pilih"
    )
    
    if not hara_pilih:
        st.warning("Pilih minimal satu unsur hara untuk dibandingkan.")
    else:
        df_npk = df_f.groupby(x_col_npk)[hara_pilih].mean().reset_index()
        df_npk_long = df_npk.melt(
            id_vars=x_col_npk,
            value_vars=hara_pilih,
            var_name="Unsur Hara",
            value_name="Nilai Rata-rata"
        )
        
        fig_npk = px.bar(
            df_npk_long,
            x=x_col_npk,
            y="Nilai Rata-rata",
            color="Unsur Hara",
            barmode="group",
            color_discrete_map={"Nitrogen": "#2563eb", "Phosphorus": "#ea580c", "Potassium": "#16a34a"}
        )
        fig_npk.update_layout(
            font=dict(family="Inter"),
            height=360,
            xaxis_title=col_x_npk,
            yaxis_title="Kandungan Hara Rata-rata",
            legend_title="Unsur Hara"
        )
        st.plotly_chart(fig_npk, use_container_width=True)

with bar_col2:
    st.markdown("### Kebutuhan Jenis Pupuk Bersubsidi")
    
    col_x_pupuk = st.radio(
        "Kelompokkan Sumbu X (Pupuk)",
        options=list(x_axis_mapping.keys()),
        horizontal=True,
        key="col_x_pupuk"
    )
    x_col_pupuk = x_axis_mapping[col_x_pupuk]
    
    pupuk_opsi_chart = sorted(df_f["Fertilizer_Name"].unique())
    pupuk_pilih_chart = st.multiselect(
        "Filter Jenis Pupuk untuk Komparasi",
        options=pupuk_opsi_chart,
        default=pupuk_opsi_chart,
        key="pupuk_pilih_chart"
    )
    
    df_pupuk_chart = df_f[df_f["Fertilizer_Name"].isin(pupuk_pilih_chart)]
    
    if df_pupuk_chart.empty:
        st.warning("Pilih minimal satu jenis pupuk.")
    else:
        pupuk_grouped = (
            df_pupuk_chart.groupby([x_col_pupuk, "Fertilizer_Name"])
            .size()
            .reset_index(name="Total_Rekomendasi")
        )

        fig_bar = px.bar(
            pupuk_grouped,
            x=x_col_pupuk,
            y="Total_Rekomendasi",
            color="Fertilizer_Name",
            barmode="group",
            labels={"Fertilizer_Name": "Jenis Pupuk", "Total_Rekomendasi": "Total Rekomendasi"},
        )
        fig_bar.update_layout(
            font=dict(family="Inter"),
            height=360, 
            xaxis_title=col_x_pupuk,
            yaxis_title="Total Rekomendasi",
            legend_title="Jenis Pupuk"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

st.markdown(
    """
    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 16px; border-radius: 8px; font-family: 'Inter', sans-serif;">
        <h5 style="color: #334155; margin-top: 0; font-family: 'Inter', sans-serif; font-weight: 700;">Analisis Kebutuhan Pupuk & Logistik</h5>
        <p style="color: #475569; font-size: 0.9em; margin-bottom: 8px; line-height: 1.45; font-family: 'Inter', sans-serif;">
            <b>Asal Data:</b> Perbandingan hara NPK dan kebutuhan pupuk di atas dihitung berdasarkan total rekomendasi kecocokan pemupukan dari data mart, dikelompokkan per kecamatan.
        </p>
        <p style="color: #475569; font-size: 0.9em; margin-bottom: 0; line-height: 1.45; font-family: 'Inter', sans-serif;">
            <b>Penyebab Pola Data:</b> UREA mendominasi karena merupakan sumber Nitrogen paling efektif untuk fase vegetatif awal tanaman pangan. Pada wilayah tanah lempung seperti <i>Pariaman Timur</i>, kebutuhan NPK lebih bervariasi karena komoditas hortikultura (sayuran & buah) yang dibudidayakan di sana membutuhkan nutrisi Fosfor dan Kalium seimbang untuk merangsang pembuahan, berbeda dengan padi sawah yang membutuhkan suplai Nitrogen masif.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.write("")
st.divider()

# ---------------------------------------------------------------------------
# TABEL PRIORITAS TINDAKAN (ACTION PRIORITIES TABLE)
# ---------------------------------------------------------------------------
st.markdown("### Tabel Prioritas Tindakan Kecamatan")
st.markdown("Berikut adalah matriks urutan prioritas wilayah beserta rekomendasi rencana tindakan taktis berdasarkan kondisi hara terendah:")

tabel_prioritas = []
for idx, row in ringkasan_kec.sort_values("pct_kritis", ascending=False).iterrows():
    kec = row["Kecamatan"]
    pct_k = row["pct_kritis"]
    
    df_kec = df_f[df_f["Kecamatan"] == kec]
    n_crit = (df_kec["Nitrogen"] < THRESHOLD_N).mean() * 100
    p_crit = (df_kec["Phosphorus"] < THRESHOLD_P).mean() * 100
    k_crit = (df_kec["Potassium"] < THRESHOLD_K).mean() * 100
    
    # Identifikasi unsur terkritis
    if n_crit >= p_crit and n_crit >= k_crit:
        hara_terkritis = "Nitrogen"
        saran_pupuk = "UREA"
        tindakan = "Penyaluran pupuk Nitrogen dan edukasi pemupukan dasar vegetatif."
    elif p_crit >= n_crit and p_crit >= k_crit:
        hara_terkritis = "Fosfor"
        saran_pupuk = "DAP / SP-36"
        tindakan = "Penyaluran SP-36/DAP untuk merangsang perakaran tanaman awal."
    else:
        hara_terkritis = "Kalium"
        saran_pupuk = "KCl / NPK"
        tindakan = "Pemberian pupuk Kalium untuk imunitas tanaman terhadap penyakit."
        
    tabel_prioritas.append({
        "Kecamatan": kec,
        "Persentase Lahan Kritis": f"{pct_k:.1f}%",
        "Kekurangan Hara Utama": hara_terkritis,
        "Pupuk Prioritas": saran_pupuk,
        "Rencana Tindakan Dinas": tindakan
    })
    
df_prioritas = pd.DataFrame(tabel_prioritas)
st.dataframe(df_prioritas, use_container_width=True, hide_index=True)
