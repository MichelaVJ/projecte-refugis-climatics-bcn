import numpy as np
import pandas as pd

RUTA_ACTUAL = "1. Data/processed/01_refugis_climatics_clean.csv"
RUTA_NOU = "1. Data/raw/opendatabcn_NP-NASIA_xarxa-refugis-climatics-csv.csv"
LLINDAR_M = 30

# ---------------------------------------------------------------------------
# 1. Dataset actual (net): corregir el bug de decimals a Latitud/Longitud
#    (les coordenades es van guardar sense el punt decimal, p.ex. 4137923.0
#    en lloc de 41.37923)
# ---------------------------------------------------------------------------
old = pd.read_csv(RUTA_ACTUAL, dtype=str)
old.columns = [c.strip().lstrip("﻿") for c in old.columns]


def fix_lat(s):
    s2 = s[:-2] if s.endswith(".0") else s.replace(".", "")
    return round(float(s2[:2] + "." + s2[2:]), 6)


def fix_lon(s):
    s2 = s[:-2] if s.endswith(".0") else s.replace(".", "")
    return round(float(s2[:1] + "." + s2[1:]), 6)


old["Latitud"] = old["Latitud"].apply(fix_lat)
old["Longitud"] = old["Longitud"].apply(fix_lon)

# ---------------------------------------------------------------------------
# 2. Dataset nou (Open Data BCN): ve en UTF-16, cal indicar l'encoding
# ---------------------------------------------------------------------------
new = pd.read_csv(RUTA_NOU, dtype=str, encoding="utf-16")
new.columns = [c.strip().lstrip("﻿") for c in new.columns]
new["register_id"] = new["register_id"].str.lstrip("﻿")

new_clean = pd.DataFrame(
    {
        "id_nou": range(1, len(new) + 1),
        "register_id": new["register_id"],
        "Nom": new["name"],
        "Adreça": new["addresses_road_name"].fillna("") + ", " + new["addresses_start_street_number"].fillna(""),
        "Barri": new["addresses_neighborhood_name"],
        "Districte": new["addresses_district_name"],
        "Latitud": new["geo_epgs_4326_lat"].astype(float).round(6),
        "Longitud": new["geo_epgs_4326_lon"].astype(float).round(6),
    }
)

# ---------------------------------------------------------------------------
# 3. Matching per distància haversina (en metres) entre tots els parells
# ---------------------------------------------------------------------------
R = 6371000  

lat1 = np.radians(old["Latitud"].values)[:, None]
lon1 = np.radians(old["Longitud"].values)[:, None]
lat2 = np.radians(new_clean["Latitud"].values)[None, :]
lon2 = np.radians(new_clean["Longitud"].values)[None, :]

dlat = lat2 - lat1
dlon = lon2 - lon1
a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
dist = 2 * R * np.arcsin(np.sqrt(a)) 


nn_new_idx = dist.argmin(axis=1)
nn_new_dist = dist.min(axis=1)

nn_old_dist = dist.min(axis=0)

# ---------------------------------------------------------------------------
# 4. Classificació
# ---------------------------------------------------------------------------
matching = old[["Nom", "Categoria", "Adreça", "Latitud", "Longitud"]].copy()
matching["Coincidencia"] = np.where(nn_new_dist <= LLINDAR_M, "Coincident", "Només al dataset actual")
matching["Nom_nou_relacionat"] = np.where(nn_new_dist <= LLINDAR_M, new_clean["Nom"].values[nn_new_idx], "")
matching["Distancia_m"] = nn_new_dist.round(1)

candidats_nous = new_clean.loc[
    nn_old_dist > LLINDAR_M, ["id_nou", "Nom", "Adreça", "Barri", "Districte", "Latitud", "Longitud"]
].copy()
candidats_nous["Distancia_al_mes_proper_actual_m"] = nn_old_dist[nn_old_dist > LLINDAR_M].round(1)

# ---------------------------------------------------------------------------
# 5. Resum i sortida
# ---------------------------------------------------------------------------
n_coincident = int((matching["Coincidencia"] == "Coincident").sum())
n_only_old = len(old) - n_coincident
n_only_new = len(candidats_nous)

print(f"Registres dataset actual: {len(old)}")
print(f"Registres dataset nou:    {len(new_clean)}")
print(f"Coincidents (<= {LLINDAR_M} m): {n_coincident}")
print(f"Només al dataset actual:  {n_only_old}")
print(f"Només al dataset nou:     {n_only_new}")

matching.to_csv("1. Data/processed/matching_complet.csv", index=False, encoding="utf-8-sig")
candidats_nous.to_csv("1. Data/processed/candidats_nous.csv", index=False, encoding="utf-8-sig")