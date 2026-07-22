"""
pages/1_Consulta_el_teu_barri.py — Pàgina 2: "Consulta el teu barri"

Flux: l'usuari selecciona el seu barri (73 opcions, tal com apareixen a les
dades) i veu la seva posició al rànquing de vulnerabilitat, indicadors
sociodemogràfics i el mapa de refugis del barri.

Nota de disseny: la proposta original demanava un input de codi postal,
però cap dels 3 datasets ni el GeoJSON de barris conté codis postals, i
BCN no té una correspondència 1:1 codi postal -> barri. S'ha substituït
per selecció directa de barri, acordat amb el propietari del projecte:
precisió total i sense necessitat de cap font addicional.
"""

import folium
import streamlit as st
from streamlit_folium import st_folium

from data_loader import (
    carrega_refugis,
    carrega_poblacio,
    carrega_renda,
    carrega_ranking,
    COL_REF_NOM,
    COL_REF_CATEGORIA,
    COL_REF_LAT,
    COL_REF_LON,
    COL_REF_ADRECA,
    COL_REF_GRATUIT,
    COL_REF_ACCES_LLIURE,
)
from utils import (
    llista_barris,
    refugis_del_barri,
    info_demografica_barri,
    estil_taula_refugis_reals,
    hex_a_rgba,
)
from estils import aplica_estil_titols, COLOR_VERD

st.set_page_config(page_title="Consulta el teu barri — Refugis BCN", layout="wide")
aplica_estil_titols()

st.title("Consulta el teu barri")
st.markdown(
    "Selecciona el teu barri per veure la seva vulnerabilitat climàtica i "
    "la cobertura real de refugis disponibles."
)

# ---------------------------------------------------------------------------
# CÀRREGA DE DADES
# ---------------------------------------------------------------------------
refugis_df = carrega_refugis()
poblacio_df = carrega_poblacio()
renda_df = carrega_renda()
ranking_df = carrega_ranking()

barris_disponibles = llista_barris(poblacio_df)

if not barris_disponibles:
    st.error(
        "No s'ha pogut carregar el llistat de barris. Comprova que el fitxer "
        "de població existeix i té la columna de nom de barri esperada."
    )
    st.stop()

# ---------------------------------------------------------------------------
# 1. INPUT: SELECCIÓ DE BARRI
# ---------------------------------------------------------------------------
barri_seleccionat = st.selectbox(
    "El teu barri:",
    options=barris_disponibles,
    index=None,
    placeholder="Selecciona un barri…",
)

if barri_seleccionat is None:
    st.info("Tria un barri de la llista per veure'n el detall.")
    st.stop()

info = info_demografica_barri(poblacio_df, renda_df, ranking_df, barri_seleccionat)

if info is None:
    st.error(
        f"No s'han trobat dades sociodemogràfiques per «{barri_seleccionat}». "
        "Comprova que el nom coincideix exactament entre datasets."
    )
    st.stop()

st.divider()

# ---------------------------------------------------------------------------
# 2. RÀNQUING DE VULNERABILITAT
# ---------------------------------------------------------------------------
if info["posicio_ranking"] is not None:
    st.subheader(barri_seleccionat)
    st.markdown(
        f"El barri **{barri_seleccionat}** ocupa la posició "
        f"**{info['posicio_ranking']} de {info['total_barris']}** "
        "barris més vulnerables climàticament de Barcelona "
        "(1 = el més vulnerable)."
    )
else:
    st.warning(
        f"No hi ha dada d'índex de vulnerabilitat disponible per «{barri_seleccionat}»."
    )

# ---------------------------------------------------------------------------
# 3. INDICADORS SOCIODEMOGRÀFICS
# ---------------------------------------------------------------------------
c1, c2, c3 = st.columns(3)
c1.metric("Població total del barri", f"{info['poblacio_total']:,}".replace(",", "."))

if info["pct_vulnerable_fisiologic"] is not None:
    c2.metric(
        "Població vulnerable (gent gran + infants)",
        f"{info['pct_vulnerable_fisiologic']:.1f}%",
    )
else:
    c2.metric("Població vulnerable (gent gran + infants)", "Dada no disponible")

if info["renda_mediana"] is not None:
    c3.metric("Renda bruta mediana per llar", f"{info['renda_mediana']:,.0f} €".replace(",", "."))
else:
    c3.metric("Renda bruta mediana per llar", "Dada no disponible")

st.divider()

# ---------------------------------------------------------------------------
# 4. REFUGIS DEL BARRI
# ---------------------------------------------------------------------------
st.subheader("Refugis climàtics al barri")

refugis_barri = refugis_del_barri(refugis_df, barri_seleccionat)

if refugis_barri.empty:
    st.warning(
        f"No hi ha cap refugi climàtic catalogat al barri «{barri_seleccionat}» "
        "a les dades disponibles."
    )
else:
    col_llista, col_mapa = st.columns([1, 1.3])

    with col_llista:
        st.markdown(f"**{len(refugis_barri)} refugis** registrats al barri:")
        columnes_mostrar = [c for c in [COL_REF_NOM, COL_REF_CATEGORIA, COL_REF_ADRECA] if c in refugis_barri.columns]

        es_real_barri = (refugis_barri[COL_REF_GRATUIT] == "Sí") & (
            refugis_barri[COL_REF_ACCES_LLIURE] == "Sí"
        )
        estil_taula_refugis = estil_taula_refugis_reals(
            refugis_barri[columnes_mostrar].reset_index(drop=True),
            es_real_barri,
            hex_a_rgba(COLOR_VERD, 0.35),
            "rgba(158, 158, 158, 0.3)",
        )
        st.dataframe(
            estil_taula_refugis,
            use_container_width=True,
            hide_index=True,
        )

    with col_mapa:
        centre_lat = refugis_barri[COL_REF_LAT].mean()
        centre_lon = refugis_barri[COL_REF_LON].mean()
        mapa = folium.Map(location=[centre_lat, centre_lon], zoom_start=15, tiles="cartodbpositron")

        # Agrupem per ubicació aproximada (arrodonida a ~11m): alguns refugis
        # comparteixen edifici però no coordenades idèntiques (p. ex. un
        # complex esportiu i la seva piscina coberta), i volem un únic
        # marcador que mostri tots els noms d'aquella ubicació, no un per fila.
        refugis_agrupar = refugis_barri.copy()
        refugis_agrupar["_lat_r"] = refugis_agrupar[COL_REF_LAT].round(4)
        refugis_agrupar["_lon_r"] = refugis_agrupar[COL_REF_LON].round(4)
        grups_ubicacio = refugis_agrupar.groupby(["_lat_r", "_lon_r"], sort=False)

        for _, grup in grups_ubicacio:
            lat = grup[COL_REF_LAT].mean()
            lon = grup[COL_REF_LON].mean()
            es_real_grup = (
                (grup[COL_REF_GRATUIT] == "Sí") & (grup[COL_REF_ACCES_LLIURE] == "Sí")
            ).any()
            color = "green" if es_real_grup else "gray"

            tooltip_html = "<br>".join(grup[COL_REF_NOM])
            popup_html = "<hr style='margin:4px 0;'>".join(
                f"<b>{fila[COL_REF_NOM]}</b><br>{fila[COL_REF_CATEGORIA]}"
                for _, fila in grup.iterrows()
            )

            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=tooltip_html,
                icon=folium.Icon(color=color, icon="thermometer-full", prefix="fa"),
            ).add_to(mapa)

        st.caption("Verd = refugi real (gratuït + accés lliure). Gris = accés limitat o de pagament.")
        st_folium(mapa, use_container_width=True, height=420, returned_objects=[])
