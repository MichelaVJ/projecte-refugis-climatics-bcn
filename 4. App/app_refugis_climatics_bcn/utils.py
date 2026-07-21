from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from data_loader import (
    COL_REF_NOM,
    COL_REF_CATEGORIA,
    COL_REF_GRATUIT,
    COL_REF_ACCES_LLIURE,
    COL_REF_LAT,
    COL_REF_LON,
    COL_REF_NOM_BARRI,
    COL_POB_NOM_BARRI,
    COL_POB_TOTAL,
    COL_POB_PCT_65,
    COL_POB_PCT_5,
    COL_RENDA_MEDIANA,
    COL_RANK_POSICIO,
    COL_RANK_PCT_VULN,
    COL_RANK_INDEX,
    COL_SIT_CODI_BARRI,
    COL_SIT_NOM_BARRI,
    COL_SIT_SITUACIO,
    COLORS_MAPA_SITUACIO,
    COLORS_QUARTIL_VULNERABILITAT,
    VALOR_SI,
)


# ---------------------------------------------------------------------------
# LLISTAT DE BARRIS
# ---------------------------------------------------------------------------
def llista_barris(poblacio_df: pd.DataFrame) -> list[str]:
    """Llista alfabètica dels 73 barris, tal com apareixen a les dades."""
    if COL_POB_NOM_BARRI not in poblacio_df.columns:
        return []
    return sorted(poblacio_df[COL_POB_NOM_BARRI].dropna().unique().tolist())


# ---------------------------------------------------------------------------
# DEDUPLICACIÓ D'UBICACIONS (mateix criteri que el notebook d'anàlisi:
# alguns refugis comparteixen coordenades exactes — p. ex. una biblioteca
# i un casal de gent gran al mateix edifici. Es deduplica per coordenades
# NOMÉS per a comptatges/percentatges agregats, mai per amagar noms a
# l'usuari.)
# ---------------------------------------------------------------------------
def refugis_unics(refugis_df: pd.DataFrame) -> pd.DataFrame:
    """Retorna una fila per ubicació física (mateixa lògica que l'informe)."""
    return refugis_df.drop_duplicates(subset=[COL_REF_LAT, COL_REF_LON])


def es_refugi_real(refugis_df: pd.DataFrame) -> pd.Series:
    """Màscara booleana: Gratuït == Sí i Accés Lliure == Sí."""
    return (refugis_df[COL_REF_GRATUIT] == VALOR_SI) & (
        refugis_df[COL_REF_ACCES_LLIURE] == VALOR_SI
    )


def refugis_reals(refugis_df: pd.DataFrame) -> pd.DataFrame:
    """Subconjunt de refugis gratuïts i d'accés lliure."""
    return refugis_df[es_refugi_real(refugis_df)]


# ---------------------------------------------------------------------------
# DADES D'UN BARRI CONCRET
# ---------------------------------------------------------------------------
def refugis_del_barri(refugis_df: pd.DataFrame, barri_nom: str) -> pd.DataFrame:
    """Tots els refugis (sense deduplicar) del barri seleccionat —
    es mostren tots els noms, encara que comparteixin ubicació física."""
    return refugis_df[refugis_df[COL_REF_NOM_BARRI] == barri_nom].copy()


def info_demografica_barri(
    poblacio_df: pd.DataFrame,
    renda_df: pd.DataFrame,
    ranking_df: pd.DataFrame,
    barri_nom: str,
) -> dict | None:
    """Recull en un sol diccionari les mètriques sociodemogràfiques del barri:
    població, % vulnerable, renda mediana, posició al rànquing de vulnerabilitat."""
    pob_fila = poblacio_df[poblacio_df[COL_POB_NOM_BARRI] == barri_nom]
    if pob_fila.empty:
        return None
    pob_fila = pob_fila.iloc[0]

    renda_fila = renda_df[renda_df[COL_POB_NOM_BARRI] == barri_nom]
    renda_mediana = renda_fila.iloc[0][COL_RENDA_MEDIANA] if not renda_fila.empty else None

    rank_fila = ranking_df[ranking_df[COL_POB_NOM_BARRI] == barri_nom]
    if not rank_fila.empty:
        rank_fila = rank_fila.iloc[0]
        posicio = int(rank_fila[COL_RANK_POSICIO])
        pct_vulnerable = float(rank_fila[COL_RANK_PCT_VULN])
        index_vulnerabilitat = float(rank_fila[COL_RANK_INDEX])
    else:
        posicio, pct_vulnerable, index_vulnerabilitat = None, None, None

    return {
        "poblacio_total": int(pob_fila[COL_POB_TOTAL]),
        "pct_65_mes": float(pob_fila[COL_POB_PCT_65]),
        "pct_menys_5": float(pob_fila[COL_POB_PCT_5]),
        "renda_mediana": renda_mediana,
        "posicio_ranking": posicio,
        "total_barris": len(ranking_df),
        "pct_vulnerable_fisiologic": pct_vulnerable,
        "index_vulnerabilitat": index_vulnerabilitat,
    }


def distribucio_categories(refugis_barri_df: pd.DataFrame) -> pd.DataFrame:
    """Distribució per categoria (a partir d'ubicacions úniques del barri),
    ordenada de més a menys freqüent."""
    unics = refugis_unics(refugis_barri_df)
    if unics.empty:
        return pd.DataFrame(columns=[COL_REF_CATEGORIA, "n"])
    return (
        unics[COL_REF_CATEGORIA]
        .value_counts()
        .rename_axis(COL_REF_CATEGORIA)
        .reset_index(name="n")
        .sort_values("n", ascending=False)
    )


def caiguda_cobertura(n_brut: int, n_filtrat: int) -> float | None:
    """Percentatge de caiguda entre el total de refugis (brut) i els que
    compleixen el criteri de 'refugi real' (gratuït + accés lliure)."""
    if n_brut == 0:
        return None
    return round((1 - n_filtrat / n_brut) * 100, 1)


# ---------------------------------------------------------------------------
# ESTADÍSTIQUES GLOBALS (per a la Pàgina 1)
# ---------------------------------------------------------------------------
def figura_mapa_vulnerabilitat_cobertura(
    situacio_df: pd.DataFrame,
    geojson_barris: dict,
    geojson_districtes: dict | None = None,
) -> "px.Figure":
    """Mapa coropleta dels 73 barris amb la mateixa classificació i colors que
    el notebook d'anàlisi (quadrant vulnerabilitat x cobertura real). En passar
    el ratolí per sobre d'un barri, apareix el seu nom. Si es passa
    `geojson_districtes`, es dibuixen a sobre els límits dels 10 districtes
    (mateix contorn que al notebook), per situar cada barri dins el seu
    districte d'un cop d'ull."""
    fig = px.choropleth(
        situacio_df,
        geojson=geojson_barris,
        locations=COL_SIT_CODI_BARRI,
        featureidkey="properties.Codi_Barri",
        color=COL_SIT_SITUACIO,
        color_discrete_map=COLORS_MAPA_SITUACIO,
        category_orders={COL_SIT_SITUACIO: list(COLORS_MAPA_SITUACIO.keys())},
        hover_name=COL_SIT_NOM_BARRI,
        hover_data={COL_SIT_CODI_BARRI: False, COL_SIT_SITUACIO: False},
    )
    
    fig.update_traces(marker_line_width=0.6, marker_line_color="white")

    if geojson_districtes is not None:
        noms_districte = [
            f["properties"]["Nom_Districte"] for f in geojson_districtes["features"]
        ]
        codis_districte = [
            f["properties"]["Codi_Districte"] for f in geojson_districtes["features"]
        ]
        fig.add_trace(
            go.Choropleth(
                geojson=geojson_districtes,
                locations=codis_districte,
                featureidkey="properties.Codi_Districte",
                z=[0] * len(codis_districte),
                colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
                showscale=False,
                marker_line_color="#91FF00",
                marker_line_width=2,
                hoverinfo="skip",
                name="Límit de districte",
                text=noms_districte,
                showlegend=False,
            )
        )

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        legend_title_text="Situació del barri",
        legend=dict(orientation="h", yanchor="top", y=-0.02, x=0, font=dict(size=11)),
        height=560,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#1C1E22",
    )
    return fig


def llindars_quartil_vulnerabilitat(ranking_df: pd.DataFrame) -> tuple[float, float]:
    """Q75 i mediana de l'índex de vulnerabilitat, calculats sobre els 73
    barris (no sobre un subconjunt filtrat), per pintar sempre amb els
    mateixos llindars que el notebook, independentment de com es filtri
    després la taula a la pantalla."""
    q75 = ranking_df[COL_RANK_INDEX].quantile(0.75)
    q50 = ranking_df[COL_RANK_INDEX].median()
    return q75, q50


def estil_ranquing_per_quartil(
    df: pd.DataFrame, col_index: str, q75: float, q50: float
):
    """Retorna un pandas Styler que pinta cada fila segons el quartil de
    l'índex de vulnerabilitat, amb els mateixos 3 colors i llindars que el
    gràfic de barres del notebook (quartil superior / 2n quartil / meitat
    inferior)."""
    colors = list(COLORS_QUARTIL_VULNERABILITAT.values())

    def color_fila(row):
        valor = row[col_index]
        if valor >= q75:
            estil = f"background-color: {colors[0]}; color: white"
        elif valor >= q50:
            estil = f"background-color: {colors[1]}; color: white"
        else:
            estil = f"background-color: {colors[2]}; color: #1a1a1a"
        return [estil] * len(row)

    return df.style.apply(color_fila, axis=1)


def hex_a_rgba(color_hex: str, alpha: float) -> str:
    """Converteix un color '#RRGGBB' a una cadena rgba(...) amb la
    transparència (alpha, 0-1) indicada."""
    color_hex = color_hex.lstrip("#")
    r, g, b = int(color_hex[0:2], 16), int(color_hex[2:4], 16), int(color_hex[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


def estil_taula_refugis_reals(
    df_mostrar: pd.DataFrame, es_real: pd.Series, color_real: str, color_no_real: str
):
    """Pinta cada fila de la taula de refugis de verd si és 'refugi real'
    (gratuït + accés lliure) o de gris si no ho és, amb el mateix criteri
    que els punts del mapa. `es_real` s'alinea per posició amb
    `df_mostrar` (independentment del seu índex)."""
    es_real = es_real.reset_index(drop=True)

    def color_fila(row):
        color = color_real if es_real.loc[row.name] else color_no_real
        return [f"background-color: {color}"] * len(row)

    return df_mostrar.style.apply(color_fila, axis=1)


def resum_global(refugis_df: pd.DataFrame) -> dict:
    """Xifres agregades per a tota Barcelona: total de refugis (ubicacions
    úniques) vs. total que compleix el criteri de 'refugi real'."""
    unics = refugis_unics(refugis_df)
    reals = refugis_reals(unics)
    total = len(unics)
    total_reals = len(reals)
    return {
        "total_refugis": total,
        "total_reals": total_reals,
        "pct_reals": round(total_reals / total * 100, 1) if total else 0,
    }
