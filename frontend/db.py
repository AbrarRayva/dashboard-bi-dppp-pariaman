"""
db.py
======
Modul helper koneksi & query ke datamart PostgreSQL (star schema
'precision_farming') yang sudah dibangun lewat notebook ETL.

Kredensial diambil dari st.secrets (lihat .streamlit/secrets.toml.example).
"""

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

SCHEMA = "precision_farming"


@st.cache_resource
def get_engine():
    """Membuat SQLAlchemy engine (di-cache agar koneksi tidak dibuat ulang)."""
    cfg = st.secrets["postgres"]
    url = (
        f"postgresql+psycopg2://{cfg['user']}:{cfg['password']}"
        f"@{cfg['host']}:{cfg['port']}/{cfg['dbname']}"
    )
    return create_engine(url, pool_pre_ping=True)


@st.cache_data(ttl=600, show_spinner="Mengambil data dari datamart...")
def load_fact_table() -> pd.DataFrame:
    """
    Mengambil tabel fakta yang sudah di-JOIN penuh dengan seluruh
    tabel dimensi (denormalized) — siap dipakai untuk semua visualisasi.
    """
    query = f"""
        SELECT
            f.id_fakta,
            w."Tanggal_Uji",
            w."Tahun",
            w."Bulan",
            w."Nama_Bulan",
            w."Kuartal",
            w."Nama_Kuartal",
            k."Nama_Kecamatan"   AS "Kecamatan",
            t."Jenis_Tanah",
            c."Jenis_Tanaman"    AS "Crop_Type",
            p."Nama_Pupuk"       AS "Fertilizer_Name",
            f."Temperature",
            f."Humidity",
            f."Moisture",
            f."Nitrogen",
            f."Phosphorus",
            f."Potassium"
        FROM "{SCHEMA}"."Fact_Evaluasi_Lahan" f
        JOIN "{SCHEMA}"."Dim_Waktu"      w ON f.id_waktu     = w.id_waktu
        JOIN "{SCHEMA}"."Dim_Kecamatan"  k ON f.id_kecamatan = k.id_kecamatan
        JOIN "{SCHEMA}"."Dim_Tanah"      t ON f.id_tanah     = t.id_tanah
        JOIN "{SCHEMA}"."Dim_Komoditas"  c ON f.id_komoditas = c.id_komoditas
        JOIN "{SCHEMA}"."Dim_Pupuk"      p ON f.id_pupuk     = p.id_pupuk
    """
    engine = get_engine()
    df = pd.read_sql(query, engine)
    df["Tanggal_Uji"] = pd.to_datetime(df["Tanggal_Uji"])
    return df


def get_db_stats():
    """Mengambil rangkuman statistik tabel dari database."""
    engine = get_engine()
    stats = {}
    with engine.connect() as conn:
        stats["total_facts"] = conn.execute(text(f'SELECT COUNT(*) FROM "{SCHEMA}"."Fact_Evaluasi_Lahan"')).scalar()
        stats["total_waktu"] = conn.execute(text(f'SELECT COUNT(*) FROM "{SCHEMA}"."Dim_Waktu"')).scalar()
        stats["total_kecamatan"] = conn.execute(text(f'SELECT COUNT(*) FROM "{SCHEMA}"."Dim_Kecamatan"')).scalar()
        stats["total_tanah"] = conn.execute(text(f'SELECT COUNT(*) FROM "{SCHEMA}"."Dim_Tanah"')).scalar()
        stats["total_komoditas"] = conn.execute(text(f'SELECT COUNT(*) FROM "{SCHEMA}"."Dim_Komoditas"')).scalar()
        stats["total_pupuk"] = conn.execute(text(f'SELECT COUNT(*) FROM "{SCHEMA}"."Dim_Pupuk"')).scalar()
        
        # Ambil rentang waktu data
        date_range = conn.execute(text(f'SELECT MIN("Tanggal_Uji"), MAX("Tanggal_Uji") FROM "{SCHEMA}"."Dim_Waktu"')).fetchone()
        stats["min_date"] = date_range[0]
        stats["max_date"] = date_range[1]
    return stats


def ingest_new_csv(df_raw: pd.DataFrame):
    """
    Mengambil data mentah (raw), memetakannya ke tabel dimensi,
    memasukkan nilai baru ke dimensi jika belum terdaftar,
    lalu memuat data baru ke tabel fakta PostgreSQL.
    """
    engine = get_engine()
    
    # 1. Standardisasi kolom (mengatasi typo penulisan/kapitalisasi dari input csv)
    col_mapping = {
        "temparature": "Temperature",
        "temperature": "Temperature",
        "humidity": "Humidity",
        "moisture": "Moisture",
        "soil type": "Soil Type",
        "crop type": "Crop Type",
        "nitrogen": "Nitrogen",
        "potassium": "Potassium",
        "phosphorous": "Phosphorus",
        "phosphorus": "Phosphorus",
        "fertilizer name": "Fertilizer Name",
        "kecamatan": "Kecamatan",
        "tanggal_uji": "Tanggal_Uji"
    }
    df = df_raw.rename(columns=lambda x: col_mapping.get(x.strip().lower(), x))
    
    # Validasi keberadaan kolom wajib
    required = ["Temperature", "Humidity", "Moisture", "Soil Type", "Crop Type", "Nitrogen", "Potassium", "Phosphorus", "Fertilizer Name"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Kolom wajib '{col}' tidak ditemukan dalam file CSV.")
            
    # Set default untuk kolom opsional jika kosong
    import datetime
    import numpy as np
    
    if "Tanggal_Uji" not in df.columns:
        df["Tanggal_Uji"] = datetime.date.today()
    else:
        df["Tanggal_Uji"] = pd.to_datetime(df["Tanggal_Uji"]).dt.date
        
    if "Kecamatan" not in df.columns:
        kecamatan_list = ["Pariaman Utara", "Pariaman Tengah", "Pariaman Selatan", "Pariaman Timur"]
        df["Kecamatan"] = np.random.choice(kecamatan_list, size=len(df))
        
    # 2. Ambil data dimensi saat ini dari DB
    with engine.connect() as conn:
        dim_waktu = pd.read_sql(f'SELECT * FROM "{SCHEMA}"."Dim_Waktu"', conn)
        dim_kecamatan = pd.read_sql(f'SELECT * FROM "{SCHEMA}"."Dim_Kecamatan"', conn)
        dim_tanah = pd.read_sql(f'SELECT * FROM "{SCHEMA}"."Dim_Tanah"', conn)
        dim_komoditas = pd.read_sql(f'SELECT * FROM "{SCHEMA}"."Dim_Komoditas"', conn)
        dim_pupuk = pd.read_sql(f'SELECT * FROM "{SCHEMA}"."Dim_Pupuk"', conn)
        
        # Ambil max ID saat ini untuk penomoran ID baru
        max_fakta_id = conn.execute(text(f'SELECT COALESCE(MAX(id_fakta), 0) FROM "{SCHEMA}"."Fact_Evaluasi_Lahan"')).scalar()
        max_waktu_id = conn.execute(text(f'SELECT COALESCE(MAX(id_waktu), 0) FROM "{SCHEMA}"."Dim_Waktu"')).scalar()
        max_tanah_id = conn.execute(text(f'SELECT COALESCE(MAX(id_tanah), 0) FROM "{SCHEMA}"."Dim_Tanah"')).scalar()
        max_komoditas_id = conn.execute(text(f'SELECT COALESCE(MAX(id_komoditas), 0) FROM "{SCHEMA}"."Dim_Komoditas"')).scalar()
        max_pupuk_id = conn.execute(text(f'SELECT COALESCE(MAX(id_pupuk), 0) FROM "{SCHEMA}"."Dim_Pupuk"')).scalar()
        
    # Map ke dictionary untuk pencarian cepat
    waktu_map = dict(zip(pd.to_datetime(dim_waktu["Tanggal_Uji"]).dt.date, dim_waktu["id_waktu"]))
    kecamatan_map = dict(zip(dim_kecamatan["Nama_Kecamatan"], dim_kecamatan["id_kecamatan"]))
    tanah_map = dict(zip(dim_tanah["Jenis_Tanah"].str.lower(), dim_tanah["id_tanah"]))
    komoditas_map = dict(zip(dim_komoditas["Jenis_Tanaman"].str.lower(), dim_komoditas["id_komoditas"]))
    pupuk_map = dict(zip(dim_pupuk["Nama_Pupuk"].str.lower(), dim_pupuk["id_pupuk"]))
    
    new_waktu_rows = []
    new_tanah_rows = []
    new_komoditas_rows = []
    new_pupuk_rows = []
    
    # 3. Cek baris per baris dan kumpulkan data dimensi baru yang belum terdaftar
    for idx, row in df.iterrows():
        tgl = row["Tanggal_Uji"]
        if hasattr(tgl, "date"):
            tgl = tgl.date()
            
        if tgl not in waktu_map:
            max_waktu_id += 1
            waktu_map[tgl] = max_waktu_id
            
            tgl_dt = pd.to_datetime(tgl)
            new_waktu_rows.append({
                "id_waktu": max_waktu_id,
                "Tanggal_Uji": tgl,
                "Tahun": int(tgl_dt.year),
                "Bulan": int(tgl_dt.month),
                "Nama_Bulan": tgl_dt.strftime("%B"),
                "Kuartal": int(tgl_dt.quarter),
                "Nama_Kuartal": f"Q{tgl_dt.quarter} {tgl_dt.year}"
            })
            
        t_name = str(row["Soil Type"]).strip()
        t_key = t_name.lower()
        if t_key not in tanah_map:
            max_tanah_id += 1
            tanah_map[t_key] = max_tanah_id
            new_tanah_rows.append({
                "id_tanah": max_tanah_id,
                "Jenis_Tanah": t_name
            })
            
        c_name = str(row["Crop Type"]).strip()
        c_key = c_name.lower()
        if c_key not in komoditas_map:
            max_komoditas_id += 1
            komoditas_map[c_key] = max_komoditas_id
            new_komoditas_rows.append({
                "id_komoditas": max_komoditas_id,
                "Jenis_Tanaman": c_name
            })
            
        p_name = str(row["Fertilizer Name"]).strip()
        p_key = p_name.lower()
        if p_key not in pupuk_map:
            max_pupuk_id += 1
            pupuk_map[p_key] = max_pupuk_id
            new_pupuk_rows.append({
                "id_pupuk": max_pupuk_id,
                "Nama_Pupuk": p_name
            })
            
    # 4. Masukkan baris dimensi baru ke PostgreSQL terlebih dahulu (untuk validasi Foreign Key)
    with engine.begin() as conn:
        if new_waktu_rows:
            conn.execute(
                text(f'INSERT INTO "{SCHEMA}"."Dim_Waktu" (id_waktu, "Tanggal_Uji", "Tahun", "Bulan", "Nama_Bulan", "Kuartal", "Nama_Kuartal") VALUES (:id_waktu, :Tanggal_Uji, :Tahun, :Bulan, :Nama_Bulan, :Kuartal, :Nama_Kuartal)'),
                new_waktu_rows
            )
        if new_tanah_rows:
            conn.execute(
                text(f'INSERT INTO "{SCHEMA}"."Dim_Tanah" (id_tanah, "Jenis_Tanah") VALUES (:id_tanah, :Jenis_Tanah)'),
                new_tanah_rows
            )
        if new_komoditas_rows:
            conn.execute(
                text(f'INSERT INTO "{SCHEMA}"."Dim_Komoditas" (id_komoditas, "Jenis_Tanaman") VALUES (:id_komoditas, :Jenis_Tanaman)'),
                new_komoditas_rows
            )
        if new_pupuk_rows:
            conn.execute(
                text(f'INSERT INTO "{SCHEMA}"."Dim_Pupuk" (id_pupuk, "Nama_Pupuk") VALUES (:id_pupuk, :Nama_Pupuk)'),
                new_pupuk_rows
            )
            
    # 5. Bangun Dataframe untuk data fakta relasional
    fact_rows = []
    for idx, row in df.iterrows():
        tgl = row["Tanggal_Uji"]
        if hasattr(tgl, "date"):
            tgl = tgl.date()
            
        t_key = str(row["Soil Type"]).strip().lower()
        c_key = str(row["Crop Type"]).strip().lower()
        p_key = str(row["Fertilizer Name"]).strip().lower()
        kec_name = row["Kecamatan"]
        
        # Defaults to 1 (Pariaman Utara) if Kecamatan name not found in standard map
        kec_id = kecamatan_map.get(kec_name, 1)
        
        max_fakta_id += 1
        fact_rows.append({
            "id_fakta": max_fakta_id,
            "id_waktu": waktu_map[tgl],
            "id_kecamatan": kec_id,
            "id_tanah": tanah_map[t_key],
            "id_komoditas": komoditas_map[c_key],
            "id_pupuk": pupuk_map[p_key],
            "Temperature": float(row["Temperature"]),
            "Humidity": float(row["Humidity"]),
            "Moisture": float(row["Moisture"]),
            "Nitrogen": int(row["Nitrogen"]),
            "Potassium": int(row["Potassium"]),
            "Phosphorus": int(row["Phosphorus"])
        })
        
    df_facts = pd.DataFrame(fact_rows)
    
    # 6. Simpan tabel fakta secara incremental ke PostgreSQL
    df_facts.to_sql(
        name="Fact_Evaluasi_Lahan",
        con=engine,
        schema=SCHEMA,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000
    )
    
    # Hapus cache data Streamlit agar data ter-update seketika
    st.cache_data.clear()
