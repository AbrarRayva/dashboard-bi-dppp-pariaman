"""
utils.py
========
Konstanta & fungsi bisnis bersama (versi Python dari "DAX Measures"
di Tahap 3 master plan):

- Ambang batas (threshold) status defisiensi hara
- Fungsi `tambah_status_defisiensi()`  -> kolom Status_Defisiensi_Hara
- Koordinat 4 kecamatan Kota Pariaman (untuk peta sebaran)
"""

import pandas as pd

# ---------------------------------------------------------------------------
# Ambang batas "Status_Defisiensi_Hara"
# Jika salah satu unsur N, P, atau K berada DI BAWAH ambang batas ini,
# maka lahan dikategorikan "Kritis". Sebaliknya "Aman".
#
# Nilai default berikut dipilih mendekati kuartil bawah (Q1) distribusi
# data N/P/K pada dataset ini. SESUAIKAN nilai ini dengan rekomendasi
# agronomis resmi (cth: Permentan) jika tersedia.
# ---------------------------------------------------------------------------
THRESHOLD_N = 7   # Nitrogen minimum
THRESHOLD_P = 7   # Phosphorus minimum
THRESHOLD_K = 1   # Potassium minimum


def hitung_status_defisiensi(nitrogen: float, phosphorus: float, potassium: float) -> str:
    """Mengembalikan 'Kritis' jika salah satu unsur N/P/K di bawah ambang batas."""
    if nitrogen < THRESHOLD_N or phosphorus < THRESHOLD_P or potassium < THRESHOLD_K:
        return "Kritis"
    return "Aman"


def tambah_status_defisiensi(df: pd.DataFrame) -> pd.DataFrame:
    """Menambahkan kolom 'Status_Defisiensi_Hara' ke dataframe fakta."""
    df = df.copy()
    df["Status_Defisiensi_Hara"] = df.apply(
        lambda row: hitung_status_defisiensi(
            row["Nitrogen"], row["Phosphorus"], row["Potassium"]
        ),
        axis=1,
    )
    return df


# ---------------------------------------------------------------------------
# Koordinat geografis 4 kecamatan Kota Pariaman (approx., untuk peta sebaran)
# Sumber: titik koordinat administratif tiap kecamatan (BPS / Pemko Pariaman)
# ---------------------------------------------------------------------------
KECAMATAN_COORDS = {
    "Pariaman Utara":   {"lat": -0.5703, "lon": 100.0987}, # Padang Birik-Birik (Kantor Camat)
    "Pariaman Tengah":  {"lat": -0.6268, "lon": 100.1333}, # Alai Gelombang (Kantor Camat)
    "Pariaman Selatan": {"lat": -0.6320, "lon": 100.1690}, # Balai Kurai Taji (Kantor Camat)
    "Pariaman Timur":   {"lat": -0.6057, "lon": 100.1493}, # Sungai Pasak (Kantor Camat)
}


def lengkapi_koordinat(df_kecamatan: pd.DataFrame, kolom_nama: str = "Kecamatan") -> pd.DataFrame:
    """Menambahkan kolom lat/lon berdasarkan nama kecamatan."""
    df_kecamatan = df_kecamatan.copy()
    df_kecamatan["lat"] = df_kecamatan[kolom_nama].map(lambda x: KECAMATAN_COORDS[x]["lat"])
    df_kecamatan["lon"] = df_kecamatan[kolom_nama].map(lambda x: KECAMATAN_COORDS[x]["lon"])
    return df_kecamatan


# Urutan kuartal kronologis (untuk sorting line chart time-series)
def urutkan_kuartal(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(["Tahun", "Kuartal"]).reset_index(drop=True)


def suntik_font_inter():
    """Injects CSS to force the Inter font globally on all Streamlit components without breaking icons."""
    import streamlit as st
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        /* Set default font on base page elements and form controls */
        html, body, input, select, textarea, button {
            font-family: 'Inter', sans-serif !important;
        }
        
        /* Restore font family for Streamlit Material Symbols / Icons */
        span[data-testid="stIconMaterial"], 
        .material-icons-sharp, 
        .material-icons-outlined, 
        .material-symbols-outlined, 
        .material-symbols-rounded, 
        .material-symbols-sharp {
            font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Symbols Sharp', 'Material Icons' !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def tampilkan_kpi_card(label: str, nilai: str, subtext: str = None):
    """Renders a premium light-themed KPI card using HTML to prevent text truncation."""
    subtext_html = f'<div style="font-size: 0.75em; color: #64748B; margin-top: 2px; font-family: \'Inter\', sans-serif;">{subtext}</div>' if subtext else ''
    card_html = f"""
    <div style="
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 14px 16px;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        height: 110px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        margin-bottom: 10px;
        font-family: 'Inter', sans-serif;
    ">
        <div style="font-size: 0.72em; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; line-height: 1.2; font-family: 'Inter', sans-serif;">
            {label}
        </div>
        <div style="font-size: 1.25em; color: #0F172A; font-weight: 700; line-height: 1.25; word-wrap: break-word; overflow-wrap: break-word; font-family: 'Inter', sans-serif;">
            {nilai}
        </div>
        {subtext_html}
    </div>
    """
    import streamlit as st
    st.markdown(card_html, unsafe_allow_html=True)

