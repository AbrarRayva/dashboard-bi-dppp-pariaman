"""
app.py
======
Entrypoint utama untuk Dashboard "Precision Farming" Kota Pariaman.
Mengatur sistem login (autentikasi) dan hak akses navigasi (role-based access control).

Menjalankan:
    streamlit run app.py
"""

import streamlit as st

# 1. Konfigurasi halaman global (harus dipanggil paling pertama di script utama)
st.set_page_config(
    page_title="Precision Farming Dashboard",
    page_icon="🌱",
    layout="wide",
)

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
    """Menampilkan form login premium."""
    # Centering login box
    c1, c2, c3 = st.columns([1, 2, 1])
    
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 20px;">
                <h1 style="color: #2E7D32;">🌱 Precision Farming</h1>
                <p style="color: #666; font-size: 1.1em;">Dinas Pertanian Kota Pariaman</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Gunakan streamlit expander/box sebagai container
        with st.container(border=True):
            st.markdown("<h3 style='text-align: center;'>Sistem Masuk (Login)</h3>", unsafe_allow_html=True)
            st.write("")
            
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
                    
        st.markdown(
            """
            <div style="text-align: center; margin-top: 20px; font-size: 0.85em; color: #888;">
                Petunjuk Kredensial Akses:<br>
                • <b>Pimpinan:</b> pimpinan / pimpinan123<br>
                • <b>Penyuluh:</b> ppl / ppl123<br>
                • <b>Admin:</b> admin / admin123
            </div>
            """, 
            unsafe_allow_html=True
        )


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
        icon="🌱",
        default=True
    )

    executive_summary_page = st.Page(
        "pages/laporan_makro_lahan.py",
        title="Laporan Makro Lahan",
        icon="📊"
    )

    precision_tool_page = st.Page(
        "pages/panduan_penyuluh_ppl.py",
        title="Panduan Penyuluh (PPL)",
        icon="🌾"
    )
    
    kelola_data_page = st.Page(
        "pages/kelola_data.py",
        title="Kelola Data",
        icon="⚙️"
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
        <div style="padding: 10px; background-color: rgba(46, 125, 50, 0.1); border-radius: 8px; margin-bottom: 15px;">
            <span style="font-size: 0.8em; color: #555; font-weight: bold; text-transform: uppercase;">Pengguna Aktif</span>
            <div style="font-weight: bold; color: #2E7D32; font-size: 1.05em;">{st.session_state.user_fullname}</div>
            <div style="font-size: 0.85em; color: #666; font-style: italic;">Peran: {st.session_state.role}</div>
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
