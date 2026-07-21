import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.stats import pearsonr, spearmanr

ARREL_PROJECTE = Path(__file__).resolve().parent.parent
DATA_PROCESSED = ARREL_PROJECTE / "1. Data" / "processed"

REFUGIS_PATH = DATA_PROCESSED / "01_refugis_climatics_amb_barri.csv"
POBLACIO_PATH = DATA_PROCESSED / "02_poblacio_barri_clean.csv"
INDEX_PATH = DATA_PROCESSED / "05_index_vulnerabilitat_barri.csv"

OUTPUT_TAXES = DATA_PROCESSED / "08_refugis_1000hab_brut_vs_filtrat.csv"
OUTPUT_PRIORITARIS = DATA_PROCESSED / "09_barris_prioritaris.csv"
OUTPUT_GRAFIC = DATA_PROCESSED / "09_vulnerabilitat_vs_cobertura.png"

# 1. Carregar dades
ref = pd.read_csv(REFUGIS_PATH)
pop = pd.read_csv(POBLACIO_PATH)
idx = pd.read_csv(INDEX_PATH)

# 2. Recompte BRUT: totes les ubicacions uniques
ref_unic = ref.drop_duplicates(subset=["Latitud", "Longitud"])
brut = ref_unic.groupby("Codi_Barri").size().rename("n_refugis_brut")

# 3. Recompte FILTRAT: nomes Gratuit=Si i Acces Lliure=Si
ref_filtrat = ref[(ref["Gratuït"] == "Sí") & (ref["Accés Lliure"] == "Sí")]
ref_filtrat_unic = ref_filtrat.drop_duplicates(subset=["Latitud", "Longitud"])
filtrat = ref_filtrat_unic.groupby("Codi_Barri").size().rename("n_refugis_filtrat")

print(f"Ubicacions uniques (brut): {len(ref_unic)}")
print(f"Ubicacions uniques (filtrat gratuit+lliure acces): {len(ref_filtrat_unic)}")

# 4. Unir amb poblacio i calcular taxes per 1.000 habitants
df = pop[["Codi_Barri", "Nom_Barri", "poblacio_total"]].merge(brut, on="Codi_Barri", how="left")
df = df.merge(filtrat, on="Codi_Barri", how="left")
df["n_refugis_brut"] = df["n_refugis_brut"].fillna(0).astype(int)
df["n_refugis_filtrat"] = df["n_refugis_filtrat"].fillna(0).astype(int)

df["taxa_brut"] = df["n_refugis_brut"] / df["poblacio_total"] * 1000
df["taxa_filtrat"] = df["n_refugis_filtrat"] / df["poblacio_total"] * 1000
df["caiguda_absoluta"] = df["taxa_brut"] - df["taxa_filtrat"]
df["caiguda_pct"] = (df["caiguda_absoluta"] / df["taxa_brut"] * 100).round(1)

# 5. Unir amb index de vulnerabilitat
df = df.merge(idx[["Codi_Barri", "index_vulnerabilitat"]], on="Codi_Barri", how="left")
assert df["index_vulnerabilitat"].isnull().sum() == 0, "Falten barris sense index"

df.to_csv(OUTPUT_TAXES, index=False, encoding="utf-8")

# 6. Correlacio entre vulnerabilitat i cobertura REAL (filtrada)
r_pearson, p_pearson = pearsonr(df["index_vulnerabilitat"], df["taxa_filtrat"])
rho, p_spearman = spearmanr(df["index_vulnerabilitat"], df["taxa_filtrat"])
print(f"\nPearson r  = {r_pearson:.3f} (p={p_pearson:.4f})")
print(f"Spearman rho = {rho:.3f} (p={p_spearman:.4f})")
if p_spearman > 0.05:
    print("-> NO estadisticament significatiu (p > 0.05)")

# 7. Barris prioritaris: quartil superior de vulnerabilitat I quartil inferior de cobertura
v_q75 = df["index_vulnerabilitat"].quantile(0.75)
c_q25 = df["taxa_filtrat"].quantile(0.25)
prioritaris = df[
    (df["index_vulnerabilitat"] >= v_q75) & (df["taxa_filtrat"] <= c_q25)
].sort_values("index_vulnerabilitat", ascending=False)

print(f"\nBarris molt vulnerables I amb poca cobertura real ({len(prioritaris)}):")
print(prioritaris[["Nom_Barri", "index_vulnerabilitat", "n_refugis_filtrat", "taxa_filtrat"]].to_string(index=False))
prioritaris.to_csv(OUTPUT_PRIORITARIS, index=False, encoding="utf-8")

# 8. Grafic de dispersio
fig, ax = plt.subplots(figsize=(8, 6.5))
mask_prio = df["Codi_Barri"].isin(prioritaris["Codi_Barri"])
ax.scatter(df.loc[~mask_prio, "index_vulnerabilitat"], df.loc[~mask_prio, "taxa_filtrat"],
           color="#7f8c8d", s=40, alpha=0.75, label="Altres barris")
ax.scatter(df.loc[mask_prio, "index_vulnerabilitat"], df.loc[mask_prio, "taxa_filtrat"],
           color="#c0392b", s=65, label="Molt vulnerables + poca cobertura real", zorder=5)

for _, row in prioritaris.iterrows():
    ax.annotate(row["Nom_Barri"], (row["index_vulnerabilitat"], row["taxa_filtrat"]),
                fontsize=7, xytext=(5, 4), textcoords="offset points")

ax.axvline(v_q75, color="black", linestyle=":", linewidth=0.6)
ax.axhline(c_q25, color="black", linestyle=":", linewidth=0.6)
ax.set_xlabel("Índex de vulnerabilitat (renda + edat)")
ax.set_ylabel("Refugis realment accessibles per 1.000 hab.\n(gratuïts + lliure accés)")
ax.set_title(f"Vulnerabilitat vs. cobertura real de refugis per barri\nCorrelació de Spearman: ρ = {rho:.2f}", fontsize=10)
ax.legend(fontsize=8)
plt.tight_layout()
plt.savefig(OUTPUT_GRAFIC, dpi=150)
print(f"\nGrafic desat a {OUTPUT_GRAFIC}")