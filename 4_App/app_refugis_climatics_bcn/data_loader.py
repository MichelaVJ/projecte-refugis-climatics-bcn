
import json
import os
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# CONSTANTS — RUTES DE FITXER
# ---------------------------------------------------------------------------
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

FITXER_REFUGIS = os.path.join(DATA_DIR, "01_refugis_climatics_amb_barri.csv")
FITXER_POBLACIO = os.path.join(DATA_DIR, "02_poblacio_barri_clean.csv")
FITXER_RENDA = os.path.join(DATA_DIR, "03_renda_bruta_llar_2023_clean.csv")
FITXER_RANKING = os.path.join(DATA_DIR, "ranking_vulnerabilitat_barris.csv")
FITXER_SITUACIO_MAPA = os.path.join(DATA_DIR, "10_situacio_vulnerabilitat_cobertura.csv")
FITXER_GEOJSON_BARRIS = os.path.join(DATA_DIR, "10_barris_geo_simplificat.geojson")
FITXER_GEOJSON_DISTRICTES = os.path.join(DATA_DIR, "10_districtes_geo_simplificat.geojson")

# ---------------------------------------------------------------------------
# CONSTANTS — NOMS DE COLUMNA
# ---------------------------------------------------------------------------
# --- Refugis ---
COL_REF_NOM = "Nom"
COL_REF_CATEGORIA = "Categoria"
COL_REF_GRATUIT = "Gratuït"
COL_REF_ACCES_LLIURE = "Accés Lliure"
COL_REF_LAT = "Latitud"
COL_REF_LON = "Longitud"
COL_REF_CODI_BARRI = "Codi_Barri"
COL_REF_NOM_BARRI = "Nom_Barri"
COL_REF_ADRECA = "Adreça"

# --- Població ---
COL_POB_CODI_BARRI = "Codi_Barri"
COL_POB_NOM_BARRI = "Nom_Barri"
COL_POB_NOM_DISTRICTE = "Nom_Districte"
COL_POB_TOTAL = "poblacio_total"
COL_POB_PCT_65 = "pct_65_mes"
COL_POB_PCT_5 = "pct_menys_5"

# --- Renda ---
COL_RENDA_CODI_BARRI = "Codi_Barri"
COL_RENDA_MEDIANA = "Renda_Bruta_Mediana"

# --- Rànquing de vulnerabilitat ---
COL_RANK_CODI_BARRI = "Codi_Barri"
COL_RANK_POSICIO = "ranking_vulnerabilitat"
COL_RANK_PCT_VULN = "pct_vulnerable_fisiologic"
COL_RANK_INDEX = "index_vulnerabilitat"

# --- Situació del mapa de vulnerabilitat i cobertura ---
COL_SIT_CODI_BARRI = "Codi_Barri"
COL_SIT_NOM_BARRI = "Nom_Barri"
COL_SIT_SITUACIO = "situacio"

# Valors que compten com "refugi real" (gratuït + accés lliure)
VALOR_SI = "Sí"

# Constants transversals
COLUMNA_BARRI_JOIN = "Nom_Barri"  # clau d'unió comuna entre tots els datasets

# Mateixos colors que el notebook d'anàlisi (02_analisi_refugis_climatics_bcn),
# secció "Vulnerabilitat vs. cobertura real de refugis climàtics, per barri"
COLORS_MAPA_SITUACIO = {
    "Crític: molt vulnerable + poca cobertura": "#C9772F",
    "Vulnerable però ben cobert": "#16324F",
    "Favorable: poc vulnerable + bona cobertura": "#7BA07E",
    "Baixa prioritat: poc vulnerable + poca cobertura": "#606060",
    "Sense dades (població < 10.000)": "#e9e8e8",
}

# Mateixos 3 colors i llindars (quartil superior / 2n quartil / meitat
# inferior) que el notebook fa servir al gràfic de barres del rànquing de
# vulnerabilitat (cel·la "Rànquing de barris per índex de vulnerabilitat")
COLORS_QUARTIL_VULNERABILITAT = {
    "Quartil superior": "#16324F",
    "2n quartil": "#3F6E8C",
    "Meitat inferior": "#9FB3BD",
}


# ---------------------------------------------------------------------------
# FUNCIONS DE CÀRREGA (cacheades)
# ---------------------------------------------------------------------------
@st.cache_data
def carrega_refugis() -> pd.DataFrame:
    """Carrega el dataset de refugis climàtics amb barri assignat."""
    df = pd.read_csv(FITXER_REFUGIS)
    return df


@st.cache_data
def carrega_poblacio() -> pd.DataFrame:
    """Carrega el dataset de població agregada per barri."""
    df = pd.read_csv(FITXER_POBLACIO)
    return df


@st.cache_data
def carrega_renda() -> pd.DataFrame:
    """Carrega el dataset de renda bruta mediana per barri."""
    df = pd.read_csv(FITXER_RENDA)
    return df


@st.cache_data
def carrega_ranking() -> pd.DataFrame:
    """Carrega el rànquing de vulnerabilitat climàtica per barri (1 = més vulnerable)."""
    df = pd.read_csv(FITXER_RANKING)
    return df


@st.cache_data
def carrega_situacio_mapa() -> pd.DataFrame:
    """Carrega la classificació per barri (quadrant vulnerabilitat x cobertura)
    que alimenta el mapa de la pàgina principal."""
    df = pd.read_csv(FITXER_SITUACIO_MAPA)
    df[COL_SIT_SITUACIO] = pd.Categorical(
        df[COL_SIT_SITUACIO], categories=list(COLORS_MAPA_SITUACIO.keys()), ordered=True
    )
    return df


@st.cache_data
def carrega_geojson_barris() -> dict:
    """Carrega la geometria dels 73 barris (versió simplificada, només
    Codi_Barri, Nom_Barri i geometria) per dibuixar el mapa."""
    with open(FITXER_GEOJSON_BARRIS, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def carrega_geojson_districtes() -> dict:
    """Carrega els límits dels 10 districtes (dissolts a partir dels barris)
    per superposar-los com a contorn sobre el mapa de barris."""
    with open(FITXER_GEOJSON_DISTRICTES, "r", encoding="utf-8") as f:
        return json.load(f)


def carrega_totes_dades() -> dict:
    """Retorna un diccionari amb els 4 dataframes ja carregats i cacheats."""
    return {
        "refugis": carrega_refugis(),
        "poblacio": carrega_poblacio(),
        "renda": carrega_renda(),
        "ranking": carrega_ranking(),
    }
