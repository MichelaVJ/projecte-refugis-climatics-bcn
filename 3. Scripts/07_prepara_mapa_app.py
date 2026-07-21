import json
from pathlib import Path

import pandas as pd
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

ARREL_PROJECTE = Path(__file__).resolve().parent.parent
DATA_PROCESSED = ARREL_PROJECTE / "1. Data" / "processed"

REFUGIS_PATH = DATA_PROCESSED / "01_refugis_climatics_amb_barri.csv"
POBLACIO_PATH = DATA_PROCESSED / "02_poblacio_barri_clean.csv"
INDEX_PATH = DATA_PROCESSED / "05_index_vulnerabilitat_barri.csv"
GEOJSON_PATH = DATA_PROCESSED / "04_barris_geo_espacial.geojson"

OUTPUT_SITUACIO = DATA_PROCESSED / "10_situacio_vulnerabilitat_cobertura.csv"
OUTPUT_GEOJSON = DATA_PROCESSED / "10_barris_geo_simplificat.geojson"
OUTPUT_GEOJSON_DISTRICTES = DATA_PROCESSED / "10_districtes_geo_simplificat.geojson"


MAPA_DISTRICTE = {
    1: "Ciutat Vella", 2: "l'Eixample", 3: "Sants-Montjuïc", 4: "Les Corts",
    5: "Sarrià-Sant Gervasi", 6: "Gràcia", 7: "Horta-Guinardó", 8: "Nou Barris",
    9: "Sant Andreu", 10: "Sant Martí",
}

LLINDAR_POBLACIO = 10000

# ---------------------------------------------------------------------------
# 1. Cobertura real (refugis "reals": Gratuït=Sí i Accés Lliure=Sí) per 1.000 hab.
# ---------------------------------------------------------------------------
refugis = pd.read_csv(REFUGIS_PATH)
poblacio = pd.read_csv(POBLACIO_PATH)
idx = pd.read_csv(INDEX_PATH)

refugis_unics = refugis.drop_duplicates(subset=["Latitud", "Longitud"])

n_filtrat = (
    refugis_unics[(refugis_unics["Gratuït"] == "Sí") & (refugis_unics["Accés Lliure"] == "Sí")]
    .groupby("Codi_Barri")
    .size()
    .rename("n_refugis_filtrat")
)

cobertura = poblacio[["Codi_Barri", "Nom_Barri", "poblacio_total"]].merge(
    n_filtrat, on="Codi_Barri", how="left"
)
cobertura["n_refugis_filtrat"] = cobertura["n_refugis_filtrat"].fillna(0).astype(int)
cobertura["taxa_1000_hab"] = cobertura["n_refugis_filtrat"] / cobertura["poblacio_total"] * 1000

cobertura_robusta = cobertura[cobertura["poblacio_total"] >= LLINDAR_POBLACIO].copy()
min_taxa = cobertura_robusta["taxa_1000_hab"].min()
max_taxa = cobertura_robusta["taxa_1000_hab"].max()
cobertura_robusta["cobertura_relativa_pct"] = (
    (cobertura_robusta["taxa_1000_hab"] - min_taxa) / (max_taxa - min_taxa) * 100
).round(1)

# ---------------------------------------------------------------------------
# 2. Creuament amb vulnerabilitat i classificació en quadrants
# ---------------------------------------------------------------------------
vuln_cobertura = idx[["Codi_Barri", "Nom_Barri", "index_vulnerabilitat"]].merge(
    cobertura_robusta[["Codi_Barri", "poblacio_total", "taxa_1000_hab", "cobertura_relativa_pct"]],
    on="Codi_Barri",
    how="inner",
)

mediana_vuln = vuln_cobertura["index_vulnerabilitat"].median()
mediana_cobertura = vuln_cobertura["cobertura_relativa_pct"].median()


def classifica_quadrant(row):
    alta_vuln = row["index_vulnerabilitat"] >= mediana_vuln
    alta_cob = row["cobertura_relativa_pct"] >= mediana_cobertura
    if alta_vuln and not alta_cob:
        return "Crític: molt vulnerable + poca cobertura"
    if alta_vuln and alta_cob:
        return "Vulnerable però ben cobert"
    if not alta_vuln and alta_cob:
        return "Favorable: poc vulnerable + bona cobertura"
    return "Baixa prioritat: poc vulnerable + poca cobertura"


vuln_cobertura["situacio"] = vuln_cobertura.apply(classifica_quadrant, axis=1)

situacio_final = idx[["Codi_Barri", "Nom_Barri", "index_vulnerabilitat"]].merge(
    vuln_cobertura[["Codi_Barri", "cobertura_relativa_pct", "situacio"]],
    on="Codi_Barri",
    how="left",
)
situacio_final["situacio"] = situacio_final["situacio"].fillna(
    "Sense dades (població < 10.000)"
)

situacio_final.to_csv(OUTPUT_SITUACIO, index=False, encoding="utf-8")
print(f"CSV de situació desat a {OUTPUT_SITUACIO} ({len(situacio_final)} barris)")
print(situacio_final["situacio"].value_counts())

# ---------------------------------------------------------------------------
# 3. Geojson simplificat (sense geopandas): només Codi_Barri, Nom_Barri i geometria
# ---------------------------------------------------------------------------
with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
    geojson_brut = json.load(f)

features_simplificades = []
for feature in geojson_brut["features"]:
    props = feature["properties"]
    features_simplificades.append(
        {
            "type": "Feature",
            "geometry": feature["geometry"],
            "properties": {
                "Codi_Barri": int(props["BARRI"]),
                "Nom_Barri": props["NOM"],
            },
        }
    )

geojson_simplificat = {"type": "FeatureCollection", "features": features_simplificades}

with open(OUTPUT_GEOJSON, "w", encoding="utf-8") as f:
    json.dump(geojson_simplificat, f, ensure_ascii=False)

print(f"Geojson simplificat desat a {OUTPUT_GEOJSON} ({len(features_simplificades)} barris)")

# ---------------------------------------------------------------------------
# 4. Límits de districte: dissolem (unim) els barris de cada districte amb
#    shapely, sense necessitat de geopandas (mateixa idea que
#    `districtes_gdf = barris_gdf.dissolve(by="Codi_Districte")` al notebook).
# ---------------------------------------------------------------------------
geometries_per_districte: dict[int, list] = {}
for feature in geojson_brut["features"]:
    props = feature["properties"]
    codi_districte = int(props["DISTRICTE"])
    geometries_per_districte.setdefault(codi_districte, []).append(shape(feature["geometry"]))

features_districtes = []
for codi_districte, geometries in sorted(geometries_per_districte.items()):
    geometria_unida = unary_union(geometries)
    features_districtes.append(
        {
            "type": "Feature",
            "geometry": mapping(geometria_unida),
            "properties": {
                "Codi_Districte": codi_districte,
                "Nom_Districte": MAPA_DISTRICTE.get(codi_districte, str(codi_districte)),
            },
        }
    )

geojson_districtes = {"type": "FeatureCollection", "features": features_districtes}

with open(OUTPUT_GEOJSON_DISTRICTES, "w", encoding="utf-8") as f:
    json.dump(geojson_districtes, f, ensure_ascii=False)

print(
    f"Geojson de districtes desat a {OUTPUT_GEOJSON_DISTRICTES} "
    f"({len(features_districtes)} districtes)"
)
