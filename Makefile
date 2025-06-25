# =======================
#      HomePedia Makefile
# =======================

PROJECT_NAME=homepedia
DOCKER=docker compose

# Chemin vers l'app Streamlit
APP_ENTRY=streamlit_app/app.py
# -- Actions globales --

all: stop clean start logs ## Redémarre tout le projet (stop → clean → start → logs)

build: ## Build toutes les images Docker
	$(DOCKER) build

start: ## Démarre les conteneurs Docker
	$(DOCKER) up -d

stop: ## Stoppe et supprime les conteneurs
	$(DOCKER) down -v

re: stop start ## Redémarre les services (équivalent à stop + start)

logs: ## Affiche les logs de tous les services
	$(DOCKER) logs -f

status: ## Affiche l'état des conteneurs
	$(DOCKER) ps

# -- Serveur Spark --

spark-master-start: ## Démarre le serveur Spark
	$(DOCKER) up -d spark-master

spark-master-stop: ## Stoppe le serveur Spark
	$(DOCKER) down -v spark-master

# -- Spark Worker --

spark-worker-start: ## Démarre le worker Spark
	$(DOCKER) up -d spark-worker

spark-worker-stop: ## Stoppe le worker Spark
	$(DOCKER) down -v spark-worker

# -- Services --

start-services: ## Démarre les services
	$(DOCKER) up -d scraper-bienici scraper-seloger scraper-gouv spark-job streamlit

stop-services: ## Stoppe les services
	$(DOCKER) down -v scraper-bienici scraper-seloger scraper-gouv spark-job streamlit

# -- Composants individuels --

run-scraper: ## Lance le scraper principal
	@echo "▶ Lancement du scraper..."
	$(DOCKER) exec -it scraper-seloger python scraper/run_seloger_spiders.py
	$(DOCKER) exec -it scraper-bienici python scraper/run_bienici_spiders.py

run-spark: ## Lance le job PySpark principal
	@echo "▶ Lancement du job PySpark..."
	$(DOCKER) run --rm spark-job

run-ui: ## Lance l'application Streamlit (UI)
	@echo "▶ Lancement de $(PROJECT_NAME) depuis $(APP_ENTRY)..."
	$(DOCKER) up -d streamlit

streamlit-stop: ## Stoppe l'application Streamlit
	$(DOCKER) down -v streamlit
	
# -- Nettoyage --

clean: ## Nettoyage des fichiers générés (raw/processed/exports)
	@echo "🧹 Nettoyage des fichiers temporaires..."
	rm -rf data/raw/*
	rm -rf data/processed/*
	rm -rf data/exports/*
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete

reset-data: ## Supprime complètement les données locales (⚠ destructif)
	@echo "⚠ Suppression complète des données locales..."
	rm -rf data/

# -- Debug & DevOps --

attach-scraper: ## Attache au conteneur scraper (manuel)
	docker attach $(PROJECT_NAME)-scraper-1

env-check: ## Affiche les variables de .env
	@echo "✅ Vérification des variables d’environnement :"
	@cat .env

export-env: ## Charge les variables .env dans l'environnement shell local
	set -a && source .env && set +a

# -- Utilitaires de dev local --

test-pyspark: ## Teste localement preprocessing Spark
	python3 spark_jobs/preprocessing.py

test-ui: ## Lance Streamlit localement hors Docker
	streamlit run streamlit_app/app.py

	lint: ## Exécute flake8 sur le projet
	flake8 streamlit_app tests

	test: ## Lance les tests unitaires
	pytest -q

# -- Meta --

help: ## Affiche cette aide
	@echo ""
	@echo "📦 Commandes disponibles :
