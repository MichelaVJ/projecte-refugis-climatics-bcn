import pandas as pd

INPUT_PATH = "03_renda_bruta_llar_2023_raw.csv"
OUTPUT_PATH = "03_renda_bruta_llar_2023_clean.csv"

# 1. Carregar dades crues (nivell secció censal)
inc = pd.read_csv(INPUT_PATH)

# 2. Agregar a nivell de barri (Codi_Barri) amb la mediana
agg = (
    inc.groupby("Codi_Barri", as_index=False)
       .agg(
           Nom_Barri=("Nom_Barri", "first"),
           Nom_Districte=("Nom_Districte", "first"),
           n_seccions=("Seccio_Censal", "count"),
           Renda_Bruta_Mediana=("Import_Renda_Bruta_€", "median"),
       )
       .sort_values("Codi_Barri")
       .reset_index(drop=True)
)

# 3. Comprovacions de qualitat
assert agg.shape[0] == 73, f"S'esperaven 73 barris, se n'han obtingut {agg.shape[0]}"
assert agg["Codi_Barri"].is_unique, "Codi_Barri té valors duplicats"
assert agg.isnull().sum().sum() == 0, "Hi ha valors nuls al resultat agregat"

# 4. Desar resultat net
agg.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")

print(f"Agregació completada: {agg.shape[0]} barris.")
print(f"Barris amb només 1 secció censal (mediana d'una sola observació):")
print(agg.loc[agg["n_seccions"] == 1, ["Codi_Barri", "Nom_Barri"]])