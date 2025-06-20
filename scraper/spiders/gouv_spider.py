import os
import gzip
import csv
from datetime import datetime
import requests
import logging
from decimal import Decimal
from typing import Dict, List

from .base_spider import RealEstateSpider
import scrapy

class GouvSpider(scrapy.Spider, RealEstateSpider):
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 1,
        'COOKIES_ENABLED': False,
    }
    """Spider pour les données immobilières du gouvernement (DVF)"""
    
    name = "gouv_spider"
    urls = [
        "https://files.data.gouv.fr/geo-dvf/latest/csv/2020/full.csv.gz",
        "https://files.data.gouv.fr/geo-dvf/latest/csv/2021/full.csv.gz",
        "https://files.data.gouv.fr/geo-dvf/latest/csv/2022/full.csv.gz",
        "https://files.data.gouv.fr/geo-dvf/latest/csv/2023/full.csv.gz",
        "https://files.data.gouv.fr/geo-dvf/latest/csv/2024/full.csv.gz"
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        RealEstateSpider.__init__(self)
        self.properties = []
        self.properties_scraped = 0
        self.properties_new = 0
        self.properties_updated = 0
        self.pages_scraped = 0
        self.start_time = datetime.now()

    def download_and_process_file(self, url: str) -> None:
        """Télécharge et traite un fichier CSV compressé"""
        try:
            # Téléchargement du fichier
            logging.info(f"Téléchargement du fichier: {url}")
            response = requests.get(url, stream=True)
            response.raise_for_status()

            # Décompression et lecture du CSV
            with gzip.open(response.raw) as gz_file:
                csv_reader = csv.DictReader(gz_file.read().decode('utf-8').splitlines(), delimiter=',')
                
                for row in csv_reader:
                    if row['nature_mutation'] == 'Vente' and row['valeur_fonciere'] and row['type_local'] in ['Maison', 'Appartement']:
                        self.process_row(row)
                        
                        # Sauvegarde par lots de 1000 propriétés
                        if len(self.properties) >= 1000:
                            self.save_properties()
                            self.properties = []

        except Exception as e:
            logging.error(f"Erreur lors du traitement du fichier {url}: {str(e)}")

    def process_row(self, row: Dict) -> None:
        """Traite une ligne du CSV et la convertit au format attendu"""
        try:
            # Calcul de la surface totale Carrez si plusieurs lots
            surface_carrez = 0
            for i in range(1, 6):
                lot_surface = row[f'lot{i}_surface_carrez']
                if lot_surface and lot_surface.strip():
                    surface_carrez += float(lot_surface)

            # Si pas de surface Carrez, utiliser surface_reelle_bati
            surface = surface_carrez or (float(row['surface_reelle_bati']) if row['surface_reelle_bati'] else 0)

            if surface <= 0:
                return

            # Construction de l'adresse complète
            address_parts = []
            if row['adresse_numero']:
                address_parts.append(row['adresse_numero'])
            if row['adresse_suffixe']:
                address_parts.append(row['adresse_suffixe'])
            if row['adresse_nom_voie']:
                address_parts.append(row['adresse_nom_voie'])
            
            address = ' '.join(address_parts)

            price = float(row['valeur_fonciere'])
            if price <= 0:
                return

            property_data = {
                'listing_url': f"dvf_{row['id_mutation']}_{row['numero_disposition']}",  # URL unique construite
                'source': self.name,
                'department': row['code_departement'],
                'price': Decimal(str(price)),
                'price_per_m2': Decimal(str(round(price / surface, 2))),
                'surface_m2': Decimal(str(surface)),
                'rooms': int(row['nombre_pieces_principales']) if row['nombre_pieces_principales'] else None,
                'bedrooms': None,  # Non disponible dans les données DVF
                'address': address,
                'city': row['nom_commune'],
                'postal_code': row['code_postal'],
                'property_type': 'maison' if row['type_local'] == 'Maison' else 'appartement',
                'features': [],
                'description': f"Mutation du {row['date_mutation']} - {row['nature_mutation']}",
                'first_seen_at': datetime.now(),
                'last_seen_at': datetime.now(),
            }

            self.properties.append(property_data)

        except Exception as e:
            logging.error(f"Erreur lors du traitement d'une ligne: {str(e)}")

    def start_requests(self) -> None:
        """Point d'entrée principal du spider"""
        try:
            for url in self.urls:
                self.download_and_process_file(url)
                
            # Sauvegarde des dernières propriétés
            if self.properties:
                self.save_properties()
                
        except Exception as e:
            logging.error(f"Erreur lors de l'exécution du spider: {str(e)}")
        finally:
            logging.info(f"Spider terminé - {self.properties_scraped} propriétés traitées "
                        f"({self.properties_new} nouvelles, {self.properties_updated} mises à jour)")
