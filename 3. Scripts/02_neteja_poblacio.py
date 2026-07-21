import pandas as pd
import os

# ─── PATHS ────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.join(os.path.dirname(__file__), "..")
INPUT_PATH = os.path.join(BASE_DIR, "1. Data", "raw", "02_poblacio_barri_raw.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "1. Data", "processed")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── CÀRREGA ──────────────────────────────────────────────────────────────────
df = pd.read_csv(INPUT_PATH)
print(f" Dataset carregat: {df.shape[0]} files × {df.shape[1]} columnes")

# ─── 1. NETEJA VALORS CONFIDENCIALS ───────────────────────────────────────────
df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0).astype(int)
print(f"   Valors confidencials ('..') convertits a 0")

# ─── 2. AGREGACIÓ PER BARRI ───────────────────────────────────────────────────
# De 46.238 files (barri × edat × sexe) a 73 files (una per barri)
resum = df.groupby(["Codi_Barri", "Nom_Barri", "Nom_Districte"]).apply(
    lambda x: pd.Series({
        "poblacio_total":   x["Valor"].sum(),
        "poblacio_65_mes":  x[x["EDAT_1"] >= 65]["Valor"].sum(),
        "poblacio_menys_5": x[x["EDAT_1"] < 5]["Valor"].sum(),
    })
).reset_index()

# ─── 3. PERCENTATGES ──────────────────────────────────────────────────────────
resum["pct_65_mes"]  = (resum["poblacio_65_mes"]  / resum["poblacio_total"] * 100).round(2)
resum["pct_menys_5"] = (resum["poblacio_menys_5"] / resum["poblacio_total"] * 100).round(2)

# ─── 4. RESUM ─────────────────────────────────────────────────────────────────
print(f"\n Resum agregació:")
print(f"   Barris: {len(resum)}")
print(f"   Població total BCN: {resum['poblacio_total'].sum():,}")

print(f"\n Majors de 65 anys:")
print(f"   min: {resum['pct_65_mes'].min():.1f}%  "
      f"max: {resum['pct_65_mes'].max():.1f}%  "
      f"mitjana: {resum['pct_65_mes'].mean():.1f}%")

print(f"\n Menors de 5 anys:")
print(f"   min: {resum['pct_menys_5'].min():.1f}%  "
      f"max: {resum['pct_menys_5'].max():.1f}%  "
      f"mitjana: {resum['pct_menys_5'].mean():.1f}%")

print(f"\n  Top 5 barris amb més gent gran:")
print(resum.nlargest(5, "pct_65_mes")[["Nom_Barri", "pct_65_mes"]].to_string(index=False))

print(f"\n Top 5 barris amb més menors de 5 anys:")
print(resum.nlargest(5, "pct_menys_5")[["Nom_Barri", "pct_menys_5"]].to_string(index=False))

# ─── 5. DESAR ─────────────────────────────────────────────────────────────────
output_path = os.path.join(OUTPUT_DIR, "02_poblacio_barri_clean.csv")
resum.to_csv(output_path, index=False, encoding="utf-8-sig")
print(f"\n Dataset net desat a: 1. Data/processed/02_poblacio_barri_clean.csv")
print(f"   {resum.shape[0]} files × {resum.shape[1]} columnes")
