# Refugis climàtics i vulnerabilitat social a Barcelona

Treball final del bootcamp d'anàlisi de dades. Estudia si la vulnerabilitat social d'un barri —renda i població de risc (gent gran i infants)— es relaciona amb la seva cobertura real de refugis climàtics, i si l'agregació oficial per districte amaga situacions de risc a escala de barri.

L'anàlisi treballa als 73 barris de Barcelona, creuant un índex de vulnerabilitat climàtica amb el nombre de refugis "reals" (gratuïts i d'accés lliure) disponibles a cada barri.

## Informe

`Informe_Refugis_Climatics.pdf` (a l'arrel del repositori) — l'informe científic complet: context, metodologia, resultats, discussió i conclusions.

## Notebook d'anàlisi

`2. Notebooks/02_analisi_refugis_climatics_bcn.ipynb` és el document central del projecte: parteix de les dades ja netes i hi conté tota l'anàlisi (índex de vulnerabilitat, cobertura real, correlació de Spearman, mapes per quadrants, barris prioritaris) amb el raonament pas a pas.

La neteja i preparació de les dades es documenta per separat a `2. Notebooks/01_neteja_preparacio_datasets.ipynb`.

## L'app

Aplicació Streamlit de dues pàgines perquè qualsevol persona pugui explorar els resultats sense obrir el notebook:

- **Resum de l'estudi** — context de l'estudi, xifres globals, rànquing de vulnerabilitat dels 73 barris i el mapa interactiu de vulnerabilitat vs. cobertura real (amb els límits de districte superposats).
- **Consulta el teu barri** — selecciones un barri i veus la seva posició al rànquing, indicadors sociodemogràfics i el mapa dels seus refugis climàtics.

Encara no està publicada; per executar-la en local:

```
cd "4. App/app_refugis_climatics_bcn"
pip install -r requirements.txt
streamlit run "Resum_de_l'estudi.py"
```

## Organització de carpetes

```
1. Data/
   raw/         Dades originals, sense modificar (Generalitat, Ajuntament, Idescat)
   processed/   Dades netes i creuades, resultat dels scripts de "3. Scripts"

2. Notebooks/
   01_neteja_preparacio_datasets.ipynb   Neteja i preparació dels 3 datasets d'origen
   02_analisi_refugis_climatics_bcn.ipynb   Anàlisi principal (vegeu més amunt)

3. Scripts/
   Versió en .py de cada pas de neteja i anàlisi del notebook, per reproduir
   el pipeline sencer de forma automàtica (numerats en ordre d'execució)

4. App/
   app_refugis_climatics_bcn/   Codi de l'app Streamlit (vegeu més amunt)

6. Grafics/
   Totes les figures generades pel notebook, en PNG, en l'ordre en què
   apareixen a l'anàlisi

Informe_Refugis_Climatics_BCN.pdf
   Informe científic final
```

## Font de les dades

- Refugis climàtics: Ajuntament de Barcelona / Generalitat de Catalunya (Open Data BCN)
- Població per barri: Ajuntament de Barcelona (Open Data BCN)
- Renda familiar disponible: Idescat
- Límits de barri (GeoJSON): Open Data BCN
