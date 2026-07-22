
import streamlit as st

from data_loader import (
    carrega_refugis,
    carrega_ranking,
    carrega_situacio_mapa,
    carrega_geojson_barris,
    carrega_geojson_districtes,
    COLORS_QUARTIL_VULNERABILITAT,
)
from utils import (
    resum_global,
    figura_mapa_vulnerabilitat_cobertura,
    llindars_quartil_vulnerabilitat,
    estil_ranquing_per_quartil,
)
from estils import aplica_estil_titols, metrica_colorida, COLOR_TEAL, COLOR_VERD, COLOR_TARONJA

# ---------------------------------------------------------------------------
# CONFIGURACIÓ DE PÀGINA
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Refugis Climàtics BCN",
    page_icon="🌡️",
    layout="wide",
)
aplica_estil_titols()

st.title("Refugis climàtics a Barcelona")
st.subheader("Quina cobertura real tenen els barris més vulnerables a la calor?")

st.markdown(
    "Aquesta aplicació acompanya un treball d'anàlisi de dades sobre la "
    "xarxa de refugis climàtics de Barcelona. Aquesta primera pàgina explica "
    "el context de l'estudi; a la pàgina **«Consulta el teu barri»** (menú "
    "de l'esquerra) pots veure la situació concreta del teu barri."
)

st.divider()

# ---------------------------------------------------------------------------
# 1. QUÈ ÉS UN REFUGI CLIMÀTIC
# ---------------------------------------------------------------------------
st.header("Què és un refugi climàtic?")

st.markdown(
    "Un **refugi climàtic** és un espai —interior o exterior— que ofereix "
    "condicions ambientals més fresques i segures durant episodis de calor "
    "extrema, i que és accessible a la ciutadania. Perque un espai es "
    "consideri un refugi climàtic complet, sol reunir algunes d'aquestes "
    "característiques:"
)

col1, col2 = st.columns(2)
with col1:
    st.markdown(
        "- 🌳 **Ombra o climatització** — arbrat dens o interiors "
        "refrigerats.\n"
        "- 💧 **Aigua potable** disponible per hidratar-se.\n"
        "- 🌬️ **Ventilació o climatització** activa a l'interior.\n"
        "- 👥 **Espais públics** i **gratuïts**."
    )
with col2:
    st.markdown(
        "- ♿ **Accessibilitat** per a persones amb mobilitat reduïda.\n"
        "- 🕒 **Horari ampli**, que cobreixi les hores de més calor.\n"
        "- 🚻 **Lavabos i àrees de descans** per a estades llargues."
    )

st.markdown(
    "Tanmateix, aquests espais haurien de proporcionar zones de refugi de llarga estada,"
    " oferint i facilitant als usuaris el desenvolupament d'activitats, sense incitar al consum."
)    

st.divider()

# ---------------------------------------------------------------------------
# 2. QUÈ ÉS UN MICROREFUGI
# ---------------------------------------------------------------------------
st.header("Què és un microrefugi climàtic?")

st.markdown(
    "Un microrefugi climàtic és un espai interior de petit format (normalment menys de 50 m²) —" \
    "com ara farmàcies, comerços o entitats— que obre les portes de manera gratuïta i accessible " \
    "perquè qualsevol persona hi pugui fer **una estada curta** i alleujar els efectes de la calor extrema. " \
    "A diferència dels grans refugis climàtics (biblioteques, parcs, centres cívics), el microrefugi ofereix " \
    "només un o pocs seients, però ha de complir requisits mínims de seguretat, accessibilitat i temperatura adequada, " \
    "i opcionalment aigua i lavabo gratuïts." \
)

st.divider()
# ---------------------------------------------------------------------------
# 2. MARC TEÒRIC / CONTEXT DE L'ESTUDI
# ---------------------------------------------------------------------------
st.header("Context: què diu la ciutat, i què hi aporta aquest estudi")

st.markdown(
    """
El canvi climàtic ha incrementat la freqüència i intensitat de les onades de calor a la conca mediterrània, 
i Barcelona no n'és una excepció. L'OMS qualifica la calor extrema *d'assassí silenciós* i identifica la gent 
gran i la infància com els grups amb més risc, per la seva menor capacitat de termoregulació (World Health Organization
 2024). Com a mesura d'adaptació, l'Ajuntament de Barcelona ha desplegat una xarxa de refugis climàtics: espais on 
 la ciutadania es pot resguardar de la calor.

El relat oficial de l'estiu de 2026 xifra la xarxa en més de 500 refugis, repartits pels 10 districtes, 
amb el 99% de la població a menys de 10 minuts a peu. Assegura, a més, que l'ampliació prioritza els barris 
amb menys cobertura i més vulnerabilitat davant la calor (<a href="https://beteve.cat/medi-ambient/mapa-refugis-climatics-barcelona/" target="_blank">Betevé, 2026</a>). 
Aquesta xifra, però, s'agrega per districte i no diferencia la qualitat d'accés real ni la contrasta amb la vulnerabilitat social de cada barri.

Aquest treball fa una radiografia dels refugis climàtics: analitza si la vulnerabilitat social d'un barri —renda i estructura 
d'edat— es relaciona amb la seva cobertura real, i si l'agregació per districte amaga situacions de 
risc a escala de barri, per prioritzar-les en properes fases d'ampliació. També posa el focus en la 
qualitat real dels refugis, no només en la seva quantitat.
""",
    unsafe_allow_html=True,
)
st.markdown(
    "**Objectiu d'aquest estudi:** les xifres agregades per districte poden "
    "amagar barris concrets desprotegits. Aquesta anàlisi treballa a escala "
    "de **barri** (73 barris), creuant un **índex de vulnerabilitat "
    "climàtica** (combinació de renda i població de risc —gent gran i "
    "infants) amb el nombre real de refugis disponibles a cada barri, per "
    "comprovar si la promesa de prioritzar els barris més vulnerables es "
    "reflecteix en la cobertura actual."
)

st.divider()

# ---------------------------------------------------------------------------
# 3. PROBLEMA DETECTAT
# ---------------------------------------------------------------------------
st.header("Filtrat de refugis")

st.markdown(
"""
En revisar el llistat oficial, molts dels espais catalogats com a refugi climàtic apareixen duplicats, 
ja que hi ha espais que formen part de la mateixa ubicació però corresponen a plantes diferents d'un mateix edifici.
Per altra banda, hem volgut filtrar la xarxa de refugis per detectar aquells que realment són gratuïts i garanteixen 
que el ciutadà s'hi pot estar una llarga durada, cosa que redueix la cobertura *real* per sota de la xifra oficial.
"""
)

st.markdown(
    "Per tenir-ho en compte, s'ha classificat cada refugi amb dos criteris:\n\n"
    "- **Gratuït**: Sí / Parcialment (context comercial sense pagament "
    "obligatori) / No (només piscines).\n"
    "- **Accés Lliure**: Sí / Parcialment (ús limitat en el temps) / "
    "Restringit (cal ser soci o usuari habitual).\n\n"
    "Es considera **\"refugi real\"** aquell que és Gratuït = Sí **i** "
    "Accés Lliure = Sí — un espai on qualsevol persona pot entrar i "
    "quedar-s'hi el temps que necessiti, sense cap barrera."
)

# --- Mètrica destacada: preview de la Pàgina 2 ---
refugis_df = carrega_refugis()
resum = resum_global(refugis_df)

st.markdown("#### En xifres, per a tot Barcelona:")
m1, m2, m3 = st.columns(3)
with m1:
    metrica_colorida(
        "Refugis climàtics catalogats",
        f"{resum['total_refugis']:,}".replace(",", "."),
        COLOR_TEAL,
    )
with m2:
    metrica_colorida(
        "...dels quals són \"refugi real\"",
        f"{resum['total_reals']:,}".replace(",", "."),
        COLOR_VERD,
    )
with m3:
    metrica_colorida(
        "Cobertura real sobre el total",
        f"{resum['pct_reals']}%",
        COLOR_TARONJA,
    )

st.caption(
    "👉 A la pàgina **«Consulta el teu barri»** pots veure aquest mateix "
    "desglossament, però pel teu barri concret."
)

st.divider()

# ---------------------------------------------------------------------------
# 3a. RÀNQUING DE VULNERABILITAT (73 BARRIS)
# ---------------------------------------------------------------------------
st.header("Rànquing de vulnerabilitat per barri")

st.markdown(
    "Abans de veure com es creua amb la cobertura real de refugis al mapa, "
    "aquest és el rànquing complet dels 73 barris segons el seu índex de "
    "vulnerabilitat climàtica (posició 1 = el més vulnerable),\n\n" \
    "L'índex s'ha calculat tenint en compte la població de risc i la renta mediana per llar.\n\n" \
    "Cerca un barri, o clica una columna per ordenar."
)

ranking_df = carrega_ranking()
q75_vuln, q50_vuln = llindars_quartil_vulnerabilitat(ranking_df)

cerca_barri = st.text_input(
    "🔍 Cerca un barri:", placeholder="Ex: Raval, Gràcia, Sarrià…"
)

ranking_mostrar = ranking_df.copy()
if cerca_barri:
    ranking_mostrar = ranking_mostrar[
        ranking_mostrar["Nom_Barri"].str.contains(cerca_barri, case=False, na=False)
    ]

COL_INDEX_MOSTRAR = "Índex de vulnerabilitat"

ranking_mostrar = ranking_mostrar[
    [
        "ranking_vulnerabilitat",
        "Nom_Barri",
        "pct_vulnerable_fisiologic",
        "Renda_Bruta_Mediana",
        "index_vulnerabilitat",
    ]
].rename(
    columns={
        "ranking_vulnerabilitat": "Posició",
        "Nom_Barri": "Barri",
        "pct_vulnerable_fisiologic": "% Vulnerable (gent gran + infants)",
        "Renda_Bruta_Mediana": "Renda mediana (€)",
        "index_vulnerabilitat": COL_INDEX_MOSTRAR,
    }
)

estil_ranquing = estil_ranquing_per_quartil(
    ranking_mostrar, COL_INDEX_MOSTRAR, q75_vuln, q50_vuln
).format(
    {
        "% Vulnerable (gent gran + infants)": "{:.1f}%".format,
        "Renda mediana (€)": lambda x: f"{x:,.0f} €".replace(",", "."),
        COL_INDEX_MOSTRAR: "{:.3f}".format,
    }
)

st.dataframe(estil_ranquing, use_container_width=True, hide_index=True, height=380)

llegenda_cols = st.columns(3)
for col, (etiqueta, color) in zip(llegenda_cols, COLORS_QUARTIL_VULNERABILITAT.items()):
    with col:
        st.markdown(
            f"<span style='display:inline-block;width:12px;height:12px;"
            f"background-color:{color};border-radius:2px;margin-right:6px;'>"
            f"</span>{etiqueta}",
            unsafe_allow_html=True,
        )

if cerca_barri and ranking_mostrar.empty:
    st.info(f"Cap barri coincideix amb «{cerca_barri}».")

st.caption(
    "👉 A la pàgina **«Consulta el teu barri»** trobaràs aquesta mateixa "
    "posició, però acompanyada del detall complet del barri triat."
)

st.divider()

# ---------------------------------------------------------------------------
# 3b. MAPA DE VULNERABILITAT I COBERTURA
# ---------------------------------------------------------------------------
st.header("Mapa de vulnerabilitat i cobertura real, barri a barri")

st.markdown(
    "Per veure d'un cop d'ull si els barris més vulnerables són també els "
    "que tenen menys refugis \"reals\", hem creuat les dues variables per "
    "als 57 barris amb prou població per fer la comparació de forma fiable "
    "(s'exclouen els 16 barris de menys de 10.000 habitants, on 1 o 2 "
    "refugis ja disparen la taxa i distorsionen la lectura).\n\n" \
    "Passa el ratolí per sobre de qualsevol barri per veure'n el nom.\n\n"
    "La línia verda marca els límits dels 10 districtes, per situar cada "
    "barri dins el seu districte."
)

situacio_df = carrega_situacio_mapa()
geojson_barris = carrega_geojson_barris()
geojson_districtes = carrega_geojson_districtes()
st.plotly_chart(
    figura_mapa_vulnerabilitat_cobertura(situacio_df, geojson_barris, geojson_districtes),
    use_container_width=True,
)

st.markdown(
    "Com es plantejava a l'inici, agregar les dades a escala de districte "
    "amagaria situacions de risc real: 5 dels 10 districtes de Barcelona "
    "(Sants-Montjuïc, les Corts, Gràcia, Sant Andreu i Sant Martí) contenen "
    "alhora com a mínim un barri en situació crítica (molt vulnerable + poca "
    "cobertura) i un altre en situació favorable. A més, 8 dels 10 districtes "
    "combinen tres o quatre situacions diferents entre els seus barris — "
    "Gràcia i Sant Martí en són els casos més extrems, amb les quatre "
    "situacions presents alhora; només Ciutat Vella i Sarrià-Sant Gervasi "
    "mostren un mínim d'homogeneïtat (dues situacions). Un indicador mitjà "
    "de districte donaria una falsa sensació de cobertura homogènia, quan en "
    "realitat conviuen barris amb necessitats molt diferents dins del mateix "
    "territori administratiu — el que reforça la necessitat de treballar a "
    "escala de barri, no de districte, per detectar zones de risc."
)

st.divider()

# ---------------------------------------------------------------------------
# 4. LIMITACIONS DE L'ESTUDI
# ---------------------------------------------------------------------------
st.header("Limitacions de l'estudi")

st.markdown(
    "Per transparència, aquestes són les principals limitacions a tenir en "
    "compte en interpretar les dades:\n\n"
    "- Les dades d'origen (Generalitat de Catalunya i Ajuntament de "
    "Barcelona) no sempre estan actualitzades al mateix ritme que la "
    "xarxa real de refugis.\n"
    "- L'**índex de vulnerabilitat** és una aproximació basada en renda i "
    "franges d'edat de risc; no inclou altres factors rellevants (salut "
    "prèvia, tipus d'habitatge, illa de calor urbana local...).\n"
    "- No es considera la **capacitat o aforament** o de cada refugi: un "
    "parc gran i un petit interior d'illa compten igual en el recompte.\n"
    "- Hi pot haver **biaixos de cobertura territorial** en les fonts "
    "originals, especialment en equipaments privats o de gestió no "
    "municipal.\n"
    "- No s'analitzen els **horaris d'obertura** dels refugis: un espai "
    "compta igual si obre 24 hores que si només obre unes poques hores "
    "al dia, tot i que això condiciona molt la seva utilitat real durant "
    "una onada de calor."
)
