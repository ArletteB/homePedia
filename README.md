# 🏠 HomePedia – Plateforme d’analyse de données immobilières

**HomePedia** est une application web de data engineering permettant de collecter, traiter et visualiser des données immobilières issues de plusieurs sources (SeLoger, Bien'ici, etc.).  
Son objectif est d’accompagner les utilisateurs dans la prise de décision immobilière grâce à une analyse claire, interactive et actualisée.

---

## 🚀 Technologies utilisées

| Composant     | Rôle                                         |
|---------------|----------------------------------------------|
| 🕷️ **Scrapy**      | Scraping des annonces immobilières           |
| 🧩 **MongoDB**     | Stockage temporaire des données brutes       |
| ⚙️ **PySpark**     | Traitement, nettoyage, analyse de données    |
| 🗃️ **PostgreSQL**  | Base de données relationnelle pour analyse   |
| 📊 **Streamlit**   | Visualisation interactive de données         |
| 📦 **Docker**      | Conteneurisation de tous les services        |

---

## 🧭 Architecture du pipeline

Scrapy (SeLoger, Bien'ici) │ ▼ MongoDB (brut) │ ▼ PySpark (nettoyage, analyse) │ ▼ PostgreSQL (standardisé) │ ▼ Streamlit (visualisation web)


---

## 📁 Structure du projet

```bash
T-DAT-902-HomePedia/
├── config/                 # Fichiers de configuration globaux (YAML)
├── data/                   # Données locales (non versionnées)
│   ├── raw/                # Données brutes Scrapy
│   ├── processed/          # Résultats Spark
│   └── exports/            # Export visuel pour Streamlit
├── database/               # Schéma SQL & collections Mongo
├── docker/                 # Dockerfiles pour chaque service
├── scraper/                # Spiders et scripts Scrapy
├── spark_jobs/            # Nettoyage, analyse, loader PySpark
├── streamlit_app/         # Interface utilisateur Streamlit
├── docker-compose.yml     # Orchestration globale
├── Makefile               # Commandes rapides (build, run, clean)
├── requirements.txt       # Dépendances Python
└── README.md              # Vous y êtes !


---

## ⚙️ Lancer le projet

### Prérequis
- Docker & Docker Compose
- Python 3.10 (optionnel pour exécutions locales)
- Certaines bibliothèques Python nécessaires à l'interface Streamlit
  (streamlit, streamlit-folium, folium, plotly, geopandas) sont listées dans
  `requirements.txt`

### Commandes utiles (via Makefile) :

```bash
make build        # Build toutes les images
make start        # Lance tous les services (Attention : peut créer des problèmes entre les services)
make stop         # Stoppe les services
make run-ui       # Démarre le conteneur Streamlit
make streamlit-stop   # Arrête le conteneur Streamlit
make clean-all    # Supprime les fichiers de données (data/)
make seed-data    # Génère des données de test JSON
make run-spark    # Exécute les jobs PySpark (recommendée après le scraping)
```


🌐 Accéder à l'application
L’interface Streamlit est disponible à l’adresse suivante une fois le projet lancé :

🔗 http://localhost:8501


📊 Fonctionnalités prévues
✅ Collecte automatisée d’annonces immobilières (Scrapy)

✅ Traitement & analyse distribuée (Spark)

✅ Visualisation dynamique des tendances prix, régions, biens

✅ Filtres interactifs, cartographies, nuages de mots

✅ Intégration PostgreSQL/Mongo + visualisation en direct

## 🔌 Connexion PostgreSQL pour Streamlit

La partie *streamlit_app* se connecte désormais directement à la base
PostgreSQL. Configurez les variables `DB_HOST`, `DB_PORT`, `DB_NAME`,
`DB_USER` et `DB_PASSWORD` (voir `.env.example`) avant de lancer
l'interface pour accéder aux données.
