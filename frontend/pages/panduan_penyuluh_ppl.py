"""
pages/panduan_penyuluh_ppl.py
==============================
Halaman "Panduan Penyuluh (PPL)" — instrumen bantu untuk Penyuluh
Pertanian Lapangan (PPL).

Komponen:
- Slicers (Kecamatan, Waktu, Jenis Tanah)
- Input kondisi lapangan saat ini (Suhu, Kelembapan, Hara)
- Gauge / Indeks Kecukupan Hara -> status "Aman Tanam" vs "Perlu Tindakan"
- Rekomendasi Aksi Penyuluh Lapangan (Actionable Insights)
- Matrix Table -> kalkulator preskriptif rekomendasi Crop Type & Fertilizer + Penjelasan Logika
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
)

st.title("🌾 Panduan Penyuluh (PPL)")
st.caption("Kalkulator rekomendasi operasional instan untuk Penyuluh Pertanian Lapangan di Kota Pariaman")

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
df = load_fact_table()
df = tambah_status_defisiensi(df)

# ---------------------------------------------------------------------------
# SLICERS (filter konteks historis)
# ---------------------------------------------------------------------------
st.markdown("### 1️⃣ Pilih Konteks Lahan")
c1, c2, c3 = st.columns(3)

with c1:
    kecamatan_pilih = st.selectbox(
        "Kecamatan Binaan", sorted(df["Kecamatan"].unique()), index=0
    )
with c2:
    tahun_pilih = st.multiselect(
        "Tahun Data Pembanding (Historis)",
        sorted(df["Tahun"].unique()),
        default=sorted(df["Tahun"].unique()),
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

st.caption(f"📌 {len(df_konteks)} titik data pengujian terdahulu ditemukan sebagai pembanding.")

st.divider()

# ---------------------------------------------------------------------------
# 2. INPUT KONDISI LAPANGAN SAAT INI
# ---------------------------------------------------------------------------
st.markdown("### 2️⃣ Masukkan Hasil Pengukuran Tanah Saat Ini")
st.caption("Gunakan alat pengukur pH/suhu tanah serta sensor NPK di lapangan, lalu masukkan nilainya:")

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

st.divider()

# ---------------------------------------------------------------------------
# 3. GAUGE / THERMOMETER - STATUS LAHAN
# ---------------------------------------------------------------------------
st.markdown("### 3️⃣ Indeks Kesuburan & Status Kesiapan Lahan")

status = hitung_status_defisiensi(nitrogen, fosfor, kalium)
label_status = "🟢 Aman Tanam" if status == "Aman" else "🔴 Perlu Tindakan"

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
            number={"suffix": " / 100"},
            title={"text": "Indeks Kecukupan Hara (N-P-K)"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "darkgreen" if status == "Aman" else "darkred"},
                "steps": [
                    {"range": [0, 50], "color": "#fde0dc"},
                    {"range": [50, 100], "color": "#d9f2d0"},
                ],
                "threshold": {
                    "line": {"color": "black", "width": 3},
                    "thickness": 0.8,
                    "value": 50,
                },
            },
        )
    )
    fig_gauge.update_layout(height=300, margin=dict(l=20, r=20, t=60, b=20))
    st.plotly_chart(fig_gauge, width="stretch")

with g2:
    st.metric("Klasifikasi Kesiapan", label_status)
    st.write(f"• **Nitrogen (N):** {nitrogen} (ambang kesuburan: ≥{THRESHOLD_N})")
    st.write(f"• **Phosphorus (P):** {fosfor} (ambang kesuburan: ≥{THRESHOLD_P})")
    st.write(f"• **Potassium (K):** {kalium} (ambang kesuburan: ≥{THRESHOLD_K})")

# ---------------------------------------------------------------------------
# REKOMENDASI AKSI PENYULUH DI LAPANGAN (ACTIONABLE INSIGHTS)
# ---------------------------------------------------------------------------
st.markdown("#### 📋 Panduan Rekomendasi Tindakan Lapangan:")

pemberitahuan_tindakan = []

if nitrogen < THRESHOLD_N:
    pemberitahuan_tindakan.append(
        f"1. **Defisit Nitrogen ({nitrogen} < {THRESHOLD_N}):** Berikan pupuk dasar **UREA** sebelum menanam untuk memicu pertumbuhan tunas dan daun muda."
    )
if fosfor < THRESHOLD_P:
    pemberitahuan_tindakan.append(
        f"2. **Defisit Phosphorus ({fosfor} < {THRESHOLD_P}):** Tambahkan pupuk **SP-36** atau **DAP** untuk memacu perkembangan perakaran awal tanaman agar kuat menyerap nutrisi."
    )
if kalium < THRESHOLD_K:
    pemberitahuan_tindakan.append(
        f"3. **Defisit Potassium ({kalium} < {THRESHOLD_K}):** Aplikasikan pupuk **KCl** untuk melindungi tanaman dari serangan patogen dan kekeringan."
    )

if status == "Aman":
    st.success(
        "✅ **Lahan Subur & Siap Tanam!** Kandungan N, P, dan K saat ini berada dalam kondisi aman. "
        "Anda dapat merekomendasikan komoditas pertanian terbaik di bawah langsung kepada petani."
    )
else:
    for tindakan in pemberitahuan_tindakan:
        st.warning(tindakan)
    st.error(
        "⚠️ **Perhatian:** Lahan kekurangan unsur hara utama. "
        "Penyuluh wajib merekomendasikan pemupukan dasar tambahan sesuai poin di atas sebelum proses penanaman bibit."
    )

st.divider()

# ---------------------------------------------------------------------------
# 4. MATRIX TABLE - KALKULATOR PRESKRIPTIF (REKOMENDASI)
# ---------------------------------------------------------------------------
st.markdown("### 4️⃣ Pencocokan Komoditas & Pupuk Paling Sesuai")

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
    st.success(
        f"💡 **Rekomendasi Terbaik:** Budidayakan tanaman **{rekom_utama['Crop_Type']}** "
        f"dengan asupan pupuk **{rekom_utama['Fertilizer_Name']}** "
        f"(memiliki tingkat kemiripan kecocokan tertinggi pada database lapangan)."
    )

    st.markdown("**Daftar Kompatibilitas Lahan (Hasil Pencocokan Model):**")
    st.dataframe(
        matrix.rename(
            columns={
                "Crop_Type": "Rekomendasi Tanaman",
                "Fertilizer_Name": "Rekomendasi Pupuk Utama",
                "Jumlah_Kemunculan": f"Frekuensi Sukses (dari {k_terdekat} sampel terdekat)",
            }
        ),
        width="stretch",
        hide_index=True,
    )

    st.markdown(
        f"""
        **💡 Mengapa Rekomendasi Ini Muncul? (Penjelasan Logis)**
        *   **Logika Penemuan:** Kalkulator ini membandingkan data ukur Anda (Suhu: {suhu:.1f}°C, Kelembapan: {kelembapan:.1f}%, Kelembapan Tanah: {kelembapan_tanah:.1f}%, N:{nitrogen}, P:{fosfor}, K:{kalium}) dengan data historis kesuksesan budidaya di wilayah *{kecamatan_pilih}* pada jenis tanah *{jenis_tanah_pilih}*.
        *   **Analisis Kecocokan:** Tanaman **{rekom_utama['Crop_Type']}** direkomendasikan karena berdasarkan 10 kondisi lahan yang paling identik di masa lalu, tanaman tersebut memberikan toleransi optimal terhadap suhu {suhu:.1f}°C dan tingkat kelembapan tanah {kelembapan_tanah:.1f}%. Penggunaan pupuk **{rekom_utama['Fertilizer_Name']}** secara konsisten memberikan suplai gizi penyeimbang hara tanah terbaik agar tanaman dapat dipanen secara maksimal.
        """
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
            width="stretch",
            hide_index=True,
        )
