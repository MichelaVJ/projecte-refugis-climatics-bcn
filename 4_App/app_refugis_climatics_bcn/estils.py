import streamlit as st

# Colors de la paleta "A · Marea"
COLOR_TITOLS = "#16324F"  # Marino
COLOR_TEAL = "#2C6E75"  # Teal · primari
COLOR_VERD = "#7BA07E"  # Salvia
COLOR_TARONJA = "#C9772F"  # Àmbar · risc


def aplica_estil_titols() -> None:
    """Pinta tots els títols (st.title, st.header, st.subheader) en blau
    marí. Cal cridar-ho un cop a cada pàgina."""
    st.markdown(
        f"""
        <style>
        h1, h2, h3 {{ color: {COLOR_TITOLS} !important; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def metrica_colorida(label: str, valor: str, color: str) -> None:
    """Mostra una mètrica amb el mateix aspecte que `st.metric`, però amb el
    número principal pintat amb el color indicat."""
    st.markdown(
        f"""
        <div style="line-height:1.2;">
            <div style="font-size:0.875rem; opacity:0.75;">{label}</div>
            <div style="font-size:2.25rem; font-weight:600; color:{color};">
                {valor}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
