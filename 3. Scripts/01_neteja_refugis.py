import pandas as pd
import os

# ─── PATHS ────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.join(os.path.dirname(__file__), "..")
INPUT_PATH = os.path.join(BASE_DIR, "1. Data", "raw", "01_refugis_climatics_raw.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "1. Data", "processed")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── CÀRREGA ──────────────────────────────────────────────────────────────────
df = pd.read_csv(INPUT_PATH)
print(f"Dataset carregat: {df.shape[0]} files × {df.shape[1]} columnes")

# ─── 1. COORDENADES ───────────────────────────────────────────────────────────
for col in ["Latitud", "Longitud"]:
    df[col] = (
        df[col]
        .astype(str)
        .str.replace(",", ".", regex=False)  
        .str.replace(r'\.(?=\d{3})', '', regex=True)  
        .astype(float)
    )

print(f"\n Coordenades convertides:")
print(f"   Latitud  → min: {df['Latitud'].min():.5f}  max: {df['Latitud'].max():.5f}")
print(f"   Longitud → min: {df['Longitud'].min():.5f}  max: {df['Longitud'].max():.5f}")

# ─── 2. DATA D'ACTUALITZACIÓ ──────────────────────────────────────────────────
df["Última Actualització"] = pd.to_datetime(
    df["Última Actualització"], dayfirst=True
)

# ─── 3. VALORS NULS ───────────────────────────────────────────────────────────
df["Climatització"] = df["Climatització"].fillna("No informat")
df["Aigua potable"] = df["Aigua potable"].fillna("No informat")

# ─── 4. ASSIGNACIÓ DE CATEGORIA ───────────────────────────────────────────────
def assigna_categoria(row):
    tipologia = row["Tipologia Refugi"]
    nom       = str(row["Nom"])
    nom_lower = nom.lower()

    # Categories directes des de la tipologia original
    mapa_directe = {
        "_microRefugi":           "Microrefugi",
        "Biblioteques":           "Biblioteca",
        "Piscines":               "Piscina",
        "Parcs i Jardins":        "Parc i Jardí",
        "Complexos esportius":    "Complex Esportiu",
        "Mercats":                "Mercat",
        "Jocs d'aigua":           "Joc d'Aigua",
        "Museus":                 "Museu",
        "Interiors d'Illa":       "Interior d'Illa",
        "Patis d'Escola":         "Pati d'Escola",
        "Patis d'Escola Bressol": "Pati d'Escola Bressol",
        "Centres de culte":       "Centre de Culte",
        "Entitats culturals":     "Entitat Cultural",
        "Comerços":               "Comerç",
        "Centres comercials":     "Centre Comercial",
        "Equipaments Ambientals": "Equipament Ambiental",
        "Equipaments de ciutat":  "Equipament de Ciutat",
    }

    if tipologia in mapa_directe:
        return mapa_directe[tipologia]

    # Tipologia "Altres" → reassignació per nom
    if tipologia == "Altres":
        if "col·legi de metges" in nom_lower or "col·legi oficial d'infermeres" in nom_lower:
            return "Equipament Sanitari"
        elif "foodcoop" in nom_lower:
            return "Comerç"
        else:
            return "Entitat Social"

    # Tipologia "Equipaments de proximitat" → desglossat per paraules clau
    if tipologia == "Equipaments de proximitat":

        # Centres Cívics
        if (nom.startswith("CC ")
                or "centre cívic" in nom_lower
                or "centre civic" in nom_lower
                or "casal cívic i comunitari" in nom_lower
                or nom.startswith("Sala ")):
            return "Centre Cívic"

        # Casals de Gent Gran
        elif (nom.startswith("CGG ")
                or "casal de gent gran" in nom_lower
                or "casal gent gran" in nom_lower
                or "casal de gg" in nom_lower
                or "espai de gent gran" in nom_lower
                or "espai gent gran" in nom_lower
                or "casal de persones grans" in nom_lower):
            return "Casal de Gent Gran"

        # Casals de Barri
        elif ("casal de barri" in nom_lower
                or "casal barri" in nom_lower
                or "casal font" in nom_lower
                or "casal mas" in nom_lower
                or "centre de vida comunitària" in nom_lower
                or "espai veïnal" in nom_lower
                or "espai comunitari" in nom_lower
                or "centre d'atenció integral" in nom_lower
                or "la lleialtat" in nom_lower):
            return "Casal de Barri"

        # Espais Jove
        elif "espai jove" in nom_lower:
            return "Espai Jove"

        # Equipaments Sanitaris
        elif ("hospital" in nom_lower
                or "clínica" in nom_lower
                or "clinica" in nom_lower
                or nom_lower.startswith("cap ")
                or " cap " in nom_lower
                or nom_lower.startswith("eap ")
                or "institut català de la salut" in nom_lower):
            return "Equipament Sanitari"

        # Farmàcies
        elif "farmàcia" in nom_lower or "farmacia" in nom_lower:
            return "Farmàcia"

        # Clubs de Petanca → Complex Esportiu
        elif nom.startswith("CPG "):
            return "Complex Esportiu"

        # Seus de Districte i Equipaments Municipals → Equipament de Ciutat
        elif ("seu districte" in nom_lower
                or "seu del districte" in nom_lower
                or "equipament municipal" in nom_lower
                or "torre jussana" in nom_lower
                or "castell de torre baró" in nom_lower
                or "centre d'informació del parc" in nom_lower
                or "la masia" in nom_lower):
            return "Equipament de Ciutat"

        # Entitats Culturals
        elif ("centre cultural" in nom_lower
                or "fabra i coats" in nom_lower
                or "centre ton i guida" in nom_lower
                or "espai montserrat" in nom_lower):
            return "Entitat Cultural"

        # Entitats Socials
        elif ("fundació" in nom_lower
                or "creu roja" in nom_lower
                or "punt d'activitat" in nom_lower
                or "casa asil" in nom_lower):
            return "Entitat Social"

        # Casa de l'Aigua → Equipament Ambiental
        elif "casa de l'aigua" in nom_lower:
            return "Equipament Ambiental"

        else:
            return "Equipament de Ciutat"

    return "Altres"


df["categoria"] = df.apply(assigna_categoria, axis=1)

print(f"\n Categories assignades:")
recompte = df["categoria"].value_counts()
for cat, n in recompte.items():
    print(f"   {cat:<25} {n:>4}")
print(f"   {'─'*30}")
print(f"   {'TOTAL':<25} {len(df):>4}")

# ─── 5. GRATUÏTAT ─────────────────────────────────────────────────────────────
mapa_gratuit = {
    "Biblioteca":             "Sí",
    "Centre Cívic":           "Sí",
    "Casal de Barri":         "Sí",
    "Casal de Gent Gran":     "Sí",
    "Espai Jove":             "Sí",
    "Mercat":                 "Parcialment",
    "Museu":                  "Parcialment",
    "Entitat Cultural":       "Sí",
    "Entitat Social":         "Sí",
    "Centre de Culte":        "Sí",
    "Parc i Jardí":           "Sí",
    "Interior d'Illa":        "Sí",
    "Joc d'Aigua":            "Sí",
    "Pati d'Escola":          "Sí",
    "Pati d'Escola Bressol":  "Sí",
    "Piscina":                "No",
    "Complex Esportiu":       "No",
    "Comerç":                 "No",
    "Centre Comercial":       "No",
    "Equipament Sanitari":    "Sí",
    "Farmàcia":               "No",
    "Equipament Ambiental":   "Sí",
    "Equipament de Ciutat":   "Sí",
    "Microrefugi":            "No",
    "Altres":                 "Parcialment",
}

df["gratuit"] = df["categoria"].map(mapa_gratuit)

# ─── 6. ACCÉS PÚBLIC ──────────────────────────────────────────────────────────
mapa_acces = {
    "Biblioteca":             "Sí",
    "Centre Cívic":           "Sí",
    "Casal de Barri":         "Sí",
    "Casal de Gent Gran":     "Restringit",
    "Espai Jove":             "Restringit",
    "Mercat":                 "Sí",
    "Museu":                  "Sí",
    "Entitat Cultural":       "Sí",
    "Entitat Social":         "Restringit",
    "Centre de Culte":        "Parcialment",
    "Parc i Jardí":           "Sí",
    "Interior d'Illa":        "Sí",
    "Joc d'Aigua":            "Sí",
    "Pati d'Escola":          "Restringit",
    "Pati d'Escola Bressol":  "Restringit",
    "Piscina":                "Sí",
    "Complex Esportiu":       "Sí",
    "Comerç":                 "Sí",
    "Centre Comercial":       "Sí",
    "Equipament Sanitari":    "Restringit",
    "Farmàcia":               "Sí",
    "Equipament Ambiental":   "Sí",
    "Equipament de Ciutat":   "Restringit",
    "Microrefugi":            "No",
    "Altres":                 "Parcialment",
}

df["acces_public"] = df["categoria"].map(mapa_acces)

# ─── 7. RESUM FINAL ───────────────────────────────────────────────────────────
print(f"\nGratuïtat:")
print(df["gratuit"].value_counts().to_string())

print(f"\nAccés públic:")
print(df["acces_public"].value_counts().to_string())

nuls_restants = df.isnull().sum()
nuls_restants = nuls_restants[nuls_restants > 0]
if len(nuls_restants) > 0:
    print(f"\nNuls restants:")
    print(nuls_restants.to_string())
else:
    print(f"\nCap valor nul a les columnes principals")

# ─── 8. DESAR ─────────────────────────────────────────────────────────────────
output_path = os.path.join(OUTPUT_DIR, "01_refugis_climatics_clean.csv")
df.to_csv(output_path, index=False, encoding="utf-8-sig")
print(f"\nDataset net desat a: 1. Data/processed/01_refugis_climatics_clean.csv")
print(f"   {df.shape[0]} files × {df.shape[1]} columnes")
