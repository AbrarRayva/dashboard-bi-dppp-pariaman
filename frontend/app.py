"""
app.py
======
Entrypoint utama untuk Dashboard "Precision Farming" Kota Pariaman.
Mengatur sistem login (autentikasi) dan hak akses navigasi (role-based access control).

Menjalankan:
    streamlit run app.py
"""

import streamlit as st
from utils import suntik_font_inter

# 1. Konfigurasi halaman global (harus dipanggil paling pertama di script utama)
st.set_page_config(
    page_title="Precision Farming Dashboard",
    layout="wide",
)
suntik_font_inter()

# Inisialisasi status login jika belum ada di session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None
    st.session_state.user_fullname = None

# Daftar user hardcoded untuk fallback aman (bisa dipindahkan ke st.secrets jika ingin lebih rahasia)
USER_CREDENTIALS = {
    "pimpinan": {
        "password": "pimpinan123",
        "role": "Pimpinan",
        "name": "Kepala Dinas Pertanian"
    },
    "ppl": {
        "password": "ppl123",
        "role": "PPL",
        "name": "Penyuluh Pertanian Lapangan"
    },
    "admin": {
        "password": "admin123",
        "role": "Admin",
        "name": "Administrator Sistem"
    }
}


def show_login_screen():
    """Menampilkan form login dengan efek frosted glass (glassmorphism) di atas mesh gradient lembut."""
    # Centering login box
    c1, c2, c3 = st.columns([1, 1.5, 1])
    
    with c2:
        # Custom CSS khusus halaman login
        st.markdown(
            """
            <style>
            /* Latar belakang dengan mesh gradient warna pertanian yang sangat lembut */
            .stApp {
                background-color: #F8FAFC !important;
                background-image: 
                    radial-gradient(at 0% 0%, rgba(220, 252, 231, 0.6) 0px, transparent 50%),
                    radial-gradient(at 100% 0%, rgba(219, 234, 254, 0.5) 0px, transparent 50%),
                    radial-gradient(at 100% 100%, rgba(254, 243, 199, 0.4) 0px, transparent 50%),
                    radial-gradient(at 0% 100%, rgba(241, 245, 249, 0.8) 0px, transparent 50%) !important;
                background-attachment: fixed !important;
            }
            [data-testid="stSidebar"] {
                display: none !important;
            }
            /* Card Kontainer Frosted Glass (Lebih melengkung halus & longgar) */
            div[data-testid="stVerticalBlockBorderWrapper"] {
                background: rgba(255, 255, 255, 0.65) !important;
                backdrop-filter: blur(20px) !important;
                -webkit-backdrop-filter: blur(20px) !important;
                border: 1px solid rgba(255, 255, 255, 0.6) !important;
                border-radius: 24px !important;
                box-shadow: 
                    0 20px 40px -15px rgba(15, 23, 42, 0.05),
                    inset 0 0 0 1px rgba(255, 255, 255, 0.5) !important;
                padding: 56px 60px !important;
            }
            /* Label Input */
            div[data-testid="stTextInput"] label {
                font-family: 'Inter', sans-serif !important;
                font-weight: 600 !important;
                color: #475569 !important;
                margin-bottom: 6px !important;
                font-size: 0.88em !important;
            }
            /* Input wrapper (menampung input & ikon mata) agar tidak terpisah */
            div[data-testid="stTextInput"] [data-baseweb="input"] {
                border-radius: 20px !important;
                border: 1px solid rgba(203, 213, 225, 0.7) !important;
                background-color: rgba(255, 255, 255, 0.7) !important;
                backdrop-filter: blur(5px) !important;
                transition: all 0.2s ease !important;
            }
            div[data-testid="stTextInput"] [data-baseweb="input"]:focus-within {
                border-color: #16A34A !important;
                box-shadow: 0 0 0 2px rgba(22, 163, 74, 0.15) !important;
                background-color: #FFFFFF !important;
            }
            
            /* Input element murni (hilangkan border bawaan agar menyatu) */
            div[data-testid="stTextInput"] input {
                border: none !important;
                background-color: transparent !important;
                font-size: 0.95em !important;
                color: #0F172A !important;
                font-family: 'Inter', sans-serif !important;
                padding: 10px 16px !important;
                box-shadow: none !important;
            }
            
            /* Merapikan posisi tombol mata agar menyatu di dalam input box */
            div[data-testid="stTextInput"] button {
                background-color: transparent !important;
                border: none !important;
                color: #475569 !important;
                margin-right: 8px !important;
            }
            
            /* Tombol Masuk (Lebih rounded) */
            button[kind="primary"] {
                background-color: #16A34A !important;
                border: none !important;
                border-radius: 20px !important;
                padding: 12px 24px !important;
                font-weight: 600 !important;
                font-size: 0.95em !important;
                color: #FFFFFF !important;
                box-shadow: 0 4px 10px rgba(22, 163, 74, 0.15) !important;
                transition: all 0.2s ease !important;
                margin-top: 12px !important;
                font-family: 'Inter', sans-serif !important;
            }
            button[kind="primary"]:hover {
                background-color: #15803D !important;
                box-shadow: 0 6px 14px rgba(22, 163, 74, 0.25) !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        
        with st.container(border=True):
            # Pastikan tidak ada indentasi markdown untuk HTML agar tidak memicu indented code block
            st.markdown(
                """<div style="text-align: center; margin-bottom: 24px;">
<div style="display: inline-flex; justify-content: center; align-items: center; background-color: rgba(22, 163, 74, 0.08); border: 1px solid rgba(22, 163, 74, 0.15); width: 48px; height: 48px; border-radius: 50%; margin-bottom: 12px;">
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#16A34A" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 3.5 0 9.8a7 7 0 0 1-8 8.2z"></path>
<path d="M9 22v-4h-4v-4H1"></path>
</svg>
</div>
<h2 style="font-weight: 800; color: #0F172A; font-family: 'Inter', sans-serif; margin: 0; font-size: 1.6em; letter-spacing: -0.5px;">Precision Farming</h2>
<p style="font-size: 0.85em; color: #16A34A; font-family: 'Inter', sans-serif; font-weight: 700; margin: 4px 0 0 0; text-transform: uppercase; letter-spacing: 1.5px;">Dinas Pertanian Kota Pariaman</p>
</div>""",
                unsafe_allow_html=True
            )
            
            username_input = st.text_input("Username", placeholder="Masukkan username Anda...")
            password_input = st.text_input("Password", type="password", placeholder="Masukkan password...")
            
            st.write("")
            submit_btn = st.button("Masuk ke Dashboard", type="primary", use_container_width=True)
            
            if submit_btn:
                u_clean = username_input.strip().lower()
                if u_clean in USER_CREDENTIALS and USER_CREDENTIALS[u_clean]["password"] == password_input:
                    st.session_state.logged_in = True
                    st.session_state.role = USER_CREDENTIALS[u_clean]["role"]
                    st.session_state.username = u_clean
                    st.session_state.user_fullname = USER_CREDENTIALS[u_clean]["name"]
                    st.success("Login berhasil! Membuka dashboard...")
                    st.rerun()
                else:
                    st.error("Username atau password salah. Silakan coba lagi.")


# ===========================================================================
# ALUR KENDALI LOG IN & NAVIGASI
# ===========================================================================

if not st.session_state.logged_in:
    show_login_screen()
else:
    # 1. Definisikan seluruh halaman aplikasi
    home_page = st.Page(
        "pages/beranda.py",
        title="Beranda",
        icon=":material/home:",
        default=True
    )

    executive_summary_page = st.Page(
        "pages/laporan_makro_lahan.py",
        title="Laporan Makro Lahan",
        icon=":material/monitoring:"
    )

    precision_tool_page = st.Page(
        "pages/panduan_penyuluh_ppl.py",
        title="Panduan Penyuluh (PPL)",
        icon=":material/agriculture:"
    )
    
    kelola_data_page = st.Page(
        "pages/kelola_data.py",
        title="Kelola Data",
        icon=":material/settings:"
    )

    # 2. Filter halaman yang dapat diakses berdasarkan Peran (Role)
    accessible_pages = [home_page]
    
    if st.session_state.role in ["Pimpinan", "Admin"]:
        accessible_pages.append(executive_summary_page)
        
    if st.session_state.role in ["PPL", "Admin"]:
        accessible_pages.append(precision_tool_page)
        
    if st.session_state.role == "Admin":
        accessible_pages.append(kelola_data_page)

    # 3. Setup header profil di bagian sidebar sebelum memuat menu
    st.sidebar.markdown(
        f"""
        <div style="padding: 12px; background-color: #F1F5F9; border: 1px solid #E2E8F0; border-radius: 8px; margin-bottom: 15px; font-family: 'Inter', sans-serif;">
            <span style="font-size: 0.75em; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; font-family: 'Inter', sans-serif;">Pengguna Aktif</span>
            <div style="font-weight: bold; color: #0F172A; font-size: 1.0em; margin-top: 2px; font-family: 'Inter', sans-serif;">{st.session_state.user_fullname}</div>
            <div style="font-size: 0.8em; color: #475569; margin-top: 1px; font-family: 'Inter', sans-serif;">Peran: {st.session_state.role}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Tombol Keluar (Logout)
    if st.sidebar.button("Keluar (Logout)", type="secondary", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.username = None
        st.session_state.user_fullname = None
        st.rerun()

    # 4. Render navigasi Streamlit
    pg = st.navigation(accessible_pages)
    pg.run()
