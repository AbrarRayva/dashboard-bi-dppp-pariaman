"""
pages/panduan_penyuluh_ppl.py
==============================
Halaman "Panduan Penyuluh (PPL)" — instrumen bantu untuk Penyuluh
Pertanian Lapangan (PPL).
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from db import load_fact_table
from utils import (
    tambah_status_defisiensi,
    hitung_status_defisiensi,
    THRESHOLD_N,
    THRESHOLD_P,
    THRESHOLD_K,
    suntik_font_inter,
)

suntik_font_inter()

st.title("Panduan Penyuluh (PPL)")
st.caption("Kalkulator rekomendasi operasional instan untuk Penyuluh Pertanian Lapangan di Kota Pariaman")
st.write("")

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
df = load_fact_table()
df = tambah_status_defisiensi(df)

# ---------------------------------------------------------------------------
# SLICERS (filter konteks historis)
# ---------------------------------------------------------------------------
st.markdown("### Pilih Konteks Lahan")
c1, c2, c3 = st.columns(3)

with c1:
    kecamatan_pilih = st.selectbox(
        "Kecamatan Binaan", sorted(df["Kecamatan"].unique()), index=0
    )
with c2:
    tahun_opsi = sorted(df["Tahun"].unique())
    tahun_pilih = st.multiselect(
        "Tahun Data Pembanding (Historis)",
        tahun_opsi,
        default=tahun_opsi,
    )
with c3:
    jenis_tanah_pilih = st.selectbox(
        "Jenis Tanah Lahan", sorted(df["Jenis_Tanah"].unique()), index=0
    )

df_konteks = df[
    (df["Kecamatan"] == kecamatan_pilih)
    & (df["Jenis_Tanah"] == jenis_tanah_pilih)
    & (df["Tahun"].isin(tahun_pilih))
]

st.caption(f"Ditemukan {len(df_konteks)} titik data pengujian terdahulu sebagai pembanding.")
st.write("")
st.divider()

# ---------------------------------------------------------------------------
# 2. INPUT KONDISI LAPANGAN SAAT INI
# ---------------------------------------------------------------------------
st.markdown("### Masukkan Hasil Pengukuran Lahan")
st.caption("Gunakan alat pengukur pH/suhu tanah serta sensor NPK di lapangan, lalu masukkan nilainya:")

with st.container(border=True):
    i1, i2, i3 = st.columns(3)
    with i1:
        suhu = st.slider("Suhu Tanah/Udara (°C)", 15.0, 45.0, float(df["Temperature"].mean()), 0.1)
        kelembapan = st.slider("Kelembapan Udara (%)", 30.0, 90.0, float(df["Humidity"].mean()), 0.1)
    with i2:
        kelembapan_tanah = st.slider("Kelembapan Tanah (%)", 10.0, 70.0, float(df["Moisture"].mean()), 0.1)
        nitrogen = st.slider("Kandungan Nitrogen (N)", 0, 50, int(df["Nitrogen"].mean()))
    with i3:
        fosfor = st.slider("Kandungan Phosphorus (P)", 0, 50, int(df["Phosphorus"].mean()))
        kalium = st.slider("Kandungan Potassium (K)", 0, 30, int(df["Potassium"].mean()))

st.write("")
st.divider()

# ---------------------------------------------------------------------------
# 3. GAUGE - STATUS LAHAN
# ---------------------------------------------------------------------------
st.markdown("### Indeks Kesuburan & Status Kesiapan Lahan")

status = hitung_status_defisiensi(nitrogen, fosfor, kalium)
label_status = "Aman Tanam" if status == "Aman" else "Perlu Tindakan"

skor = np.mean([
    min(nitrogen / THRESHOLD_N, 2) * 50,
    min(fosfor / THRESHOLD_P, 2) * 50,
    min(kalium / THRESHOLD_K, 2) * 50,
])
skor = float(np.clip(skor, 0, 100))

g1, g2 = st.columns([2, 1])

with g1:
    fig_gauge = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=skor,
            number={"suffix": " / 100", "font": {"color": "#0F172A"}},
            title={"text": "Indeks Kecukupan Hara (N-P-K)", "font": {"color": "#0F172A"}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#0F172A"},
                "bar": {"color": "#15803d" if status == "Aman" else "#b91c1c"},
                "steps": [
                    {"range": [0, 50], "color": "#fee2e2"},
                    {"range": [50, 100], "color": "#dcfce7"},
                ],
                "threshold": {
                    "line": {"color": "#0F172A", "width": 3},
                    "thickness": 0.8,
                    "value": 50,
                },
            },
        )
    )
    fig_gauge.update_layout(
        font=dict(family="Inter"),
        height=300, 
        margin=dict(l=20, r=20, t=60, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

with g2:
    with st.container(border=True):
        st.metric("Klasifikasi Kesiapan", label_status)
        st.markdown(
            f"""
            <div style="font-size: 0.9em; line-height: 1.6; color: #334155;">
                • <b>Nitrogen (N):</b> {nitrogen} <span style="color: #64748B;">(ambang: ≥{THRESHOLD_N})</span><br>
                • <b>Fosfor (P):</b> {fosfor} <span style="color: #64748B;">(ambang: ≥{THRESHOLD_P})</span><br>
                • <b>Kalium (K):</b> {kalium} <span style="color: #64748B;">(ambang: ≥{THRESHOLD_K})</span>
            </div>
            """,
            unsafe_allow_html=True
        )

# ---------------------------------------------------------------------------
# REKOMENDASI AKSI PENYULUH DI LAPANGAN
# ---------------------------------------------------------------------------
st.markdown("#### Panduan Rekomendasi Tindakan Lapangan")

if status == "Aman":
    st.markdown(
        """
        <div style="background-color: #F0FDF4; border-left: 4px solid #10B981; padding: 16px; border-radius: 4px; margin-bottom: 15px;">
            <p style="color: #064E3B; margin: 0; font-size: 0.95em;">
                <b>Lahan Subur & Siap Tanam:</b> Kandungan hara Nitrogen, Fosfor, dan Kalium saat ini berada dalam kondisi aman. 
                Anda dapat merekomendasikan komoditas pertanian terbaik di bawah langsung kepada petani.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    pemberitahuan_tindakan = []
    if nitrogen < THRESHOLD_N:
        pemberitahuan_tindakan.append(
            f"<li><b>Defisit Nitrogen ({nitrogen} < {THRESHOLD_N}):</b> Berikan pupuk dasar <b>UREA</b> sebelum menanam untuk memicu pertumbuhan tunas dan daun muda.</li>"
        )
    if fosfor < THRESHOLD_P:
        pemberitahuan_tindakan.append(
            f"<li><b>Defisit Fosfor ({fosfor} < {THRESHOLD_P}):</b> Tambahkan pupuk <b>SP-36</b> atau <b>DAP</b> untuk memacu perkembangan perakaran awal tanaman baru agar kuat menyerap nutrisi.</li>"
        )
    if kalium < THRESHOLD_K:
        pemberitahuan_tindakan.append(
            f"<li><b>Defisit Kalium ({kalium} < {THRESHOLD_K}):</b> Aplikasikan pupuk <b>KCl</b> untuk melindungi tanaman dari serangan patogen dan efek kekeringan.</li>"
        )
        
    tindakan_html = "".join(pemberitahuan_tindakan)
    st.markdown(
        f"""
        <div style="background-color: #FFFBEB; border-left: 4px solid #F59E0B; padding: 16px; border-radius: 4px; margin-bottom: 15px;">
            <p style="color: #78350F; margin: 0 0 8px 0; font-weight: bold; font-size: 0.95em;">Lahan Kekurangan Unsur Hara Utama</p>
            <ul style="color: #78350F; margin: 0; padding-left: 20px; font-size: 0.9em; line-height: 1.5;">
                {tindakan_html}
            </ul>
        </div>
        """,
        unsafe_allow_html=True
    )

st.write("")
st.divider()

# ---------------------------------------------------------------------------
# 4. MATRIX TABLE - KALKULATOR PRESKRIPTIF
# ---------------------------------------------------------------------------
st.markdown("### Pencocokan Komoditas & Pupuk Paling Sesuai")

if len(df_konteks) == 0:
    st.warning("Tidak ada data historis untuk kombinasi Kecamatan + Jenis Tanah ini. Coba sesuaikan filter di atas.")
else:
    # Normalisasi fitur agar skala sebanding, lalu hitung jarak Euclidean
    fitur = ["Temperature", "Humidity", "Moisture", "Nitrogen", "Phosphorus", "Potassium"]
    input_vector = np.array([suhu, kelembapan, kelembapan_tanah, nitrogen, fosfor, kalium])

    data_fitur = df_konteks[fitur].to_numpy(dtype=float)
    rentang = data_fitur.max(axis=0) - data_fitur.min(axis=0)
    rentang[rentang == 0] = 1

    data_norm = (data_fitur - data_fitur.min(axis=0)) / rentang
    input_norm = (input_vector - data_fitur.min(axis=0)) / rentang

    jarak = np.linalg.norm(data_norm - input_norm, axis=1)

    df_konteks_jarak = df_konteks.copy()
    df_konteks_jarak["jarak"] = jarak

    k_terdekat = min(10, len(df_konteks_jarak))
    tetangga_terdekat = df_konteks_jarak.nsmallest(k_terdekat, "jarak")

    matrix = (
        tetangga_terdekat.groupby(["Crop_Type", "Fertilizer_Name"])
        .agg(Jumlah_Kemunculan=("jarak", "size"), Rata_Jarak=("jarak", "mean"))
        .reset_index()
        .sort_values(["Jumlah_Kemunculan", "Rata_Jarak"], ascending=[False, True])
        .reset_index(drop=True)
    )

    jarak_maks = max(tetangga_terdekat["jarak"].max(), 1e-9)
    matrix["Skor_Kecocokan (%)"] = ((1 - matrix["Rata_Jarak"] / jarak_maks) * 100).clip(0, 100).round(1)
    matrix = matrix.drop(columns="Rata_Jarak")

    rekom_utama = matrix.iloc[0]
    
    st.markdown(
        f"""
        <div style="background-color: #ECFDF5; border: 1px solid #A7F3D0; padding: 16px; border-radius: 8px; margin-bottom: 15px;">
            <p style="color: #047857; margin: 0; font-size: 0.95em;">
                <b>Rekomendasi Terbaik:</b> Budidayakan tanaman <b>{rekom_utama['Crop_Type']}</b> 
                dengan asupan pupuk utama <b>{rekom_utama['Fertilizer_Name']}</b> 
                (memiliki tingkat kemiripan kecocokan tertinggi pada database pengujian historis).
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("##### Daftar Kompatibilitas Lahan (Hasil Pencocokan Model)")
    st.dataframe(
        matrix.rename(
            columns={
                "Crop_Type": "Rekomendasi Tanaman",
                "Fertilizer_Name": "Rekomendasi Pupuk Utama",
                "Jumlah_Kemunculan": f"Frekuensi Sukses (dari {k_terdekat} sampel terdekat)",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown(
        f"""
        <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 16px; border-radius: 8px; margin-top: 15px;">
            <h5 style="color: #334155; margin-top: 0; font-family: 'sans serif';">Penjelasan Logika Pencocokan</h5>
            <p style="color: #475569; font-size: 0.9em; margin-bottom: 8px; line-height: 1.45;">
                <b>Logika Penemuan:</b> Kalkulator membandingkan data ukur lapangan Anda (Suhu: {suhu:.1f}°C, Kelembapan: {kelembapan:.1f}%, Kelembapan Tanah: {kelembapan_tanah:.1f}%, N: {nitrogen}, P: {fosfor}, K: {kalium}) dengan data historis di database pada wilayah <i>{kecamatan_pilih}</i> dan jenis tanah <i>{jenis_tanah_pilih}</i>.
            </p>
            <p style="color: #475569; font-size: 0.9em; margin-bottom: 0; line-height: 1.45;">
                <b>Analisis Kecocokan:</b> Tanaman <b>{rekom_utama['Crop_Type']}</b> direkomendasikan karena berdasarkan {k_terdekat} kondisi lahan yang paling mirip di masa lalu, komoditas tersebut memberikan toleransi optimal terhadap suhu {suhu:.1f}°C dan kelembapan tanah {kelembapan_tanah:.1f}%. Penggunaan pupuk <b>{rekom_utama['Fertilizer_Name']}</b> terbukti memberikan suplai nutrisi penyeimbang hara tanah terbaik agar komoditas tersebut dapat dipanen secara maksimal.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.expander("Lihat 10 titik data historis pembanding terdekat"):
        st.dataframe(
            tetangga_terdekat[
                ["Tanggal_Uji", "Crop_Type", "Fertilizer_Name", "Temperature", "Humidity", "Moisture", "Nitrogen", "Phosphorus", "Potassium", "jarak"]
            ].rename(columns={
                "jarak": "Skor Selisih Karakteristik (Makin kecil = makin identik)",
                "Crop_Type": "Jenis Tanaman",
                "Fertilizer_Name": "Jenis Pupuk"
            }),
            use_container_width=True,
            hide_index=True,
        )
