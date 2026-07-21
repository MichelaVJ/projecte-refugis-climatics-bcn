import pandas as pd

pop = pd.read_csv("1. Data/processed/02_poblacio_barri_clean.csv")
inc = pd.read_csv("1. Data/processed/03_renda_bruta_llar_2023_clean.csv")

# 1. Unir població i renda per Codi_Barri
df = pop.merge(
    inc[["Codi_Barri", "Renda_Bruta_Mediana"]],
    on="Codi_Barri",
    how="left"
)

# 2. Indicador demogràfic combinat (gent gran 65+ i infants <5)

df["pct_vulnerable_fisiologic"] = df["pct_65_mes"] + df["pct_menys_5"]

# 3. Normalització per percentil
df["renda_percentil"] = df["Renda_Bruta_Mediana"].rank(pct=True)
df["edat_percentil"] = df["pct_vulnerable_fisiologic"].rank(pct=True)

# 4. Índex compost: 50% renda invertida + 50% edat de risc
df["index_vulnerabilitat"] = (
    0.5 * (1 - df["renda_percentil"]) + 0.5 * df["edat_percentil"]
)

df = df.sort_values("index_vulnerabilitat", ascending=False)
df.to_csv("1. Data/processed/05_index_vulnerabilitat_barri.csv", index=False, encoding="utf-8")