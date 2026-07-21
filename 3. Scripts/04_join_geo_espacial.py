import geopandas as gpd
import pandas as pd
from pathlib import Path
from shapely.geometry import Point


ARREL_PROJECTE = Path(__file__).resolve().parent.parent
DATA_PROCESSED = ARREL_PROJECTE / "1. Data" / "processed"

REFUGIS_PATH = DATA_PROCESSED / "01_refugis_climatics_clean.csv"
BARRIS_PATH = DATA_PROCESSED / "04_barris_geo_espacial.geojson"
OUTPUT_PATH = DATA_PROCESSED / "01_refugis_climatics_amb_barri.csv"

# 1. Carregar refugis i convertir-los en GeoDataFrame de punts (WGS84 = EPSG:4326)
refugis = pd.read_csv(REFUGIS_PATH)
geometria_punts = [Point(lon, lat) for lon, lat in zip(refugis["Longitud"], refugis["Latitud"])]
refugis_gdf = gpd.GeoDataFrame(refugis, geometry=geometria_punts, crs="EPSG:4326")

# 2. Carregar poligons de barri (ja venen en WGS84)
barris_gdf = gpd.read_file(BARRIS_PATH)
barris_gdf = barris_gdf[["BARRI", "NOM", "DISTRICTE", "geometry"]].rename(
    columns={"BARRI": "Codi_Barri", "NOM": "Nom_Barri", "DISTRICTE": "Codi_Districte"}
)
barris_gdf["Codi_Barri"] = barris_gdf["Codi_Barri"].astype(int)

# 3. Join espacial: per a cada refugi, quin poligon de barri el conte
resultat = gpd.sjoin(refugis_gdf, barris_gdf, how="left", predicate="within")

# 4. Comprovacio 1: refugis que no han encaixat a cap poligon (frontera/error GPS)
sense_barri = resultat[resultat["Codi_Barri"].isna()]
print(f"Refugis sense barri assignat (within): {len(sense_barri)}")

if len(sense_barri) > 0:
    # Solucio de reserva: assignar el barri mes proper (distancia al poligon mes propera)
    refugis_sense_barri = refugis_gdf.loc[sense_barri.index]
    reassignats = gpd.sjoin_nearest(refugis_sense_barri, barris_gdf, how="left")
    resultat.loc[sense_barri.index, ["Codi_Barri", "Nom_Barri", "Codi_Districte"]] = (
        reassignats[["Codi_Barri", "Nom_Barri", "Codi_Districte"]].values
    )
    print(f"  -> reassignats al barri mes proper amb sjoin_nearest")

# 5. Comprovacio 2: cap refugi duplicat (p.ex. per caure justa sobre una frontera compartida)
n_original = len(refugis)
n_resultat = len(resultat)
print(f"Files originals: {n_original} | Files despres del join: {n_resultat}")
if n_resultat > n_original:
    print("ATENCIO: hi ha refugis duplicats (probablement per caure sobre una frontera).")
    duplicats = resultat[resultat.duplicated(subset=["Nom", "Latitud", "Longitud"], keep=False)]
    print(duplicats[["Nom", "Latitud", "Longitud", "Codi_Barri", "Nom_Barri"]])
    # Es recomana revisar manualment aquests casos abans de continuar.

# 6. Comprovacio 3: cap Codi_Barri nul despres del fallback
assert resultat["Codi_Barri"].isna().sum() == 0, "Encara queden refugis sense Codi_Barri"

# 7. Desar resultat (nomes columnes rellevants, sense les internes de geopandas)
columnes_finals = [c for c in refugis.columns] + ["Codi_Barri", "Nom_Barri", "Codi_Districte"]
resultat[columnes_finals].to_csv(OUTPUT_PATH, index=False, encoding="utf-8")

print(f"\nFet. Guardat a {OUTPUT_PATH}")
print(resultat["Nom_Barri"].value_counts().head(10))