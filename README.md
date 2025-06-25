# 🏠 HomePedia – Plateforme d’analyse de données immobilières

**HomePedia** est une application web de data engineering permettant de **collecter**, **traiter** et **visualiser** des données immobilières issues de plusieurs sources (SeLoger, Bien'ici, etc.).
Son objectif est d’accompagner les utilisateurs (particuliers & professionnels) dans la prise de décision immobilière grâce à une analyse claire, interactive et constamment actualisée.

---

## 🚀 Technologies utilisées

| Composant          | Rôle                                             |
| ------------------ | ------------------------------------------------ |
| 🕷️ **Scrapy**     | Scraping des annonces immobilières               |
| 🧩 **MongoDB**     | Stockage temporaire des données brutes           |
| ⚙️ **PySpark**     | Traitement, nettoyage et préparation des données |
| 🗃️ **PostgreSQL** | Base de données relationnelle pour l’analyse     |
| 📊 **Streamlit**   | Visualisation interactive & tableau de bord      |
| 📦 **Docker**      | Conteneurisation de tous les services            |

---

## 🧭 Architecture du pipeline

```
Scrapy (SeLoger, Bien'ici)  ─►  MongoDB (brut)  ─►  PySpark (traitement)  ─►  PostgreSQL (standardisé)  ─►  Streamlit (visualisation)
```

---

## 📁 Structure du projet

```bash
T-DAT-902-HomePedia/
├── config/                 # Configurations globales (YAML)
├── database/               # Schémas SQL & collections Mongo
├── docker/                 # Dockerfiles par service
├── scraper/                # Spiders & scripts Scrapy
├── spark_jobs/             # Nettoyage, analyse, loader PySpark
├── streamlit_app/          # Interface Streamlit
│   ├── app.py              # Point d’entrée
│   ├── pages/
│   │   ├── analyse_description.py
│   │   ├── analyse_globale.py
│   │   ├── carte_interactive.py
│   │   ├── catalogue.py
│   │   └── tendance_temps.py
│   ├── components/
│   │   └── sidebar.py
│   ├── utils/
│   │   └── db_connection.py
│   ├── config.py
│   └── assets/
├── docker-compose.yml      # Orchestration globale
├── Makefile                # Commandes (build, run, clean…)
├── requirements.txt        # Dépendances Python
└── README.md               # (vous y êtes)
```

---

## ⚙️ Lancer le projet

### Prérequis

* Docker & Docker Compose
* Python ≥ 3.10 (optionnel pour exécution locale)
* Dépendances listées dans `requirements.txt` (Streamlit, Folium, PyDeck, Plotly, GeoPandas…)

### Commandes Makefile clés

```bash
make build            # Build des images Docker
make start            # Démarrage de l’ensemble des services
make stop             # Arrêt complet
make run-ui           # Lancement du conteneur Streamlit
make streamlit-stop   # Arrêt de l’UI Streamlit
make clean-all        # Suppression des données (data/)
make seed-data        # Injection de données de test JSON
make run-spark        # Exécution des jobs PySpark
```

---

## 🔌 Connexion PostgreSQL pour Streamlit

La partie **streamlit\_app** se connecte à PostgreSQL. Renseignez les variables d’environnement `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` (voir `.env.example`) avant de lancer l’interface.

---

## 🎯 Problématique

> **Quels critères influencent le plus les prix du marché ?**
>
> Analyse nationale des facteurs :
>
> * Nombre d’offres
> * Type de bien
> * Localisation
> * Surface habitable (m²)
> * Nombre de chambres

---

## 📊 Visualisation (Streamlit) – Spécifications minimales

La couche de visualisation s’appuie sur **Streamlit** et répond aux exigences pédagogiques fixées :

| Exigence            | Implémentation HomePedia                                                                    |
| ------------------- | ------------------------------------------------------------------------------------------- |
| Map **obligatoire** | 3 cartes distinctes : choroplèthe prix / heatmap densité d’offres / bubble‑map surface‑prix |
| Bar chart           | Histogramme comparant l’influence relative des critères sur le prix                         |
| Filtre clair        | Widgets Streamlit libellés en langage métier pour un agent immobilier                       |
| Titre explicite     | Chaque graphique possède un titre indiquant la question traitée                             |
| Intérêt propre      | Chaque visuel répond à une sous‑question de la problématique                                |

### 📌 Catalogue de visuels

1. **Carte choroplèthe nationale – Prix moyen au m²**

   * *Question :* « Où les prix au m² sont‑ils les plus élevés ? »
   * *Filtres :* année / gamme de prix

2. **Heatmap densité d’offres**

   * *Question :* « Quelles zones concentrent le plus grand nombre d’annonces ? »
   * *Filtres :* type de bien / tranche de prix

3. **Bubble‑map surface ↔ prix**

   * *Question :* « Comment le prix varie‑t‑il selon la surface moyenne par commune ? »
   * *Filtre :* tranche de surface

4. **Bar chart – Importance des critères**

   * *Question :* « Quels facteurs expliquent le mieux la variation du prix ? »
   * *Données :* score d’influence (corrélation ou feature importance) pour chacun des critères étudiés

### ⚙️ Fonctionnalités interactives

* **Filtres dynamiques** (`selectbox`, `multiselect`, `slider`…) appliqués à l’ensemble des visuels.
* **Réactivité** : mises à jour temps‑réel lors des changements de filtre.
* **Navigation multi‑niveaux** : national ➜ régional ➜ départemental ➜ communal.
* **Design épuré** : pas de chartjunk, titres & légendes explicites.

---

## 📈 Feuille de route / Fonctionnalités réalisées

* ✅ Collecte automatisée d’annonces immobilières (Scrapy)
* ✅ Traitement & analyse distribuée (PySpark)
* ✅ Intégration PostgreSQL/Mongo + chargement continu
* ✅ Visualisations interactives (cartes, bar chart, filtres dynamiques, nuages de mots)
* 🔄 **À venir** : déploiement cloud & authentification utilisateur

---

## 🌐 Accéder à l’application

## ▶️ Lancer l'interface Streamlit

### Option 1 – universelle (Windows)
Sur le terminal :
```bash
./run_streamlit.bat

Une fois lancés : **[http://localhost:8501](http://localhost:8501)**

---

> *“Transformez les données brutes du marché immobilier en insights exploitables – visuellement, interactivement, instantanément.”*


### 🗺️ Intégration Mapbox

HomePedia utilise **Mapbox** pour la génération de cartes interactives haute qualité.  
Une clé API valide est requise (déjà disponible pour ce projet).

- Compatible avec `pydeck`, `folium` et `deck.gl`
- Cartes choroplèthes, heatmaps, points dynamiques
- Affichage fluide, responsive et hautement personnalisable

> ℹ️ La clé API est stockée via variable d’environnement : `MAPBOX_API_KEY` (cf. `.env.example`)
