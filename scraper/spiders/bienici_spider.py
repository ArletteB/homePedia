import os
from datetime import datetime, timedelta
from urllib.parse import urljoin
import logging
from spiders.base_spider import RealEstateSpider

import pymongo
import scrapy
import requests
import json
import decimal
# Configuration du logger
# logging.basicConfig(level=logging.DEBUG)

# Désactiver les logs de debug MongoDB
logging.getLogger('pymongo').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('pyspark').setLevel(logging.WARNING)
from pyspark.sql import SparkSession
from pyspark.conf import SparkConf
import signal

from dotenv import load_dotenv
import os

# Charger les variables d'environnement
load_dotenv()

# Configuration MongoDB
MONGO_CONFIG = {
    'host': os.getenv('MONGO_HOST', 'localhost'),
    'port': int(os.getenv('MONGO_PORT', '27017')),
    'database': os.getenv('MONGO_DB', 'homepedia_db'),
    'user': os.getenv('MONGO_USER', 'admin'),
    'password': os.getenv('MONGO_PASSWORD', 'admin')
}

class BienIciSpider(RealEstateSpider, scrapy.Spider):
    name = "bienici_spider"
    allowed_domains = ["bienici.com"]
    MIN_PAGES = int(os.getenv('MIN_PAGES', 1))
    MAX_PAGES = int(os.getenv('MAX_PAGES', 100))
    PAGE_SIZE = int(os.getenv('PAGE_SIZE', 25))
    
    # Track progress
    properties_scraped = 0
    properties_new = 0
    properties_updated = 0
    pages_scraped = 0
    start_time = None
    _shutdown_requested = False
    checkpoint_location = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        signal.signal(signal.SIGINT, self._handle_sigint)

        # Initialiser la session Spark
        self.logger.info('Initialisation de la session Spark...')
        self.checkpoint_location = self.get_checkpoint_location()
        # Configuration de la session Spark
        conf = SparkConf() \
            .setAppName("BienIciScraper") \
            .setMaster(os.environ.get("SPARK_MASTER", "local[*]")) \
            .set("spark.driver.memory", "2g") \
            .set("spark.executor.memory", "2g") \
            .set("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.2.1")

        self.spark = SparkSession.builder \
            .config(conf=conf) \
            .getOrCreate()

        self.logger.info("Spark session created successfully.")
        # Initialiser une liste pour stocker les propriétés
        self.properties = []

    def _handle_sigint(self, signum, frame):
        self.logger.info("Received SIGINT, saving remaining properties and stats...")
        self._shutdown_requested = True
        if self.properties:
            self.save_properties()
        self.save_stats()
        self.logger.info("Saved all remaining data. Shutting down...")
        sys.exit(0)

    cookies = {
        'AB-TESTING': '%7B%22relatedAdsPosition%22%3A%22relatedAdsAfterSlideShow%22%7D',
        'i18next': 'fr',
        '_pcid': '%7B%22browserId%22%3A%22m6jib25m4xudrdun%22%2C%22_t%22%3A%22mm7x8ji7%7Cm6jib267%22%7D',
        '_pctx': '%7Bu%7DN4IgrgzgpgThIC4B2YA2qA05owMoBcBDfSREQpAeyRCwgEt8oBJAE0RXSwH18yBbfgHYAHgA4AVvSEAffgDYpAIwBM8oSAC%2BQA',
        '_gcl_au': '1.1.1754802178.1738251916',
        '_pprv': 'eyJjb25zZW50Ijp7IjAiOnsibW9kZSI6Im9wdC1pbiJ9LCIxIjp7Im1vZGUiOiJvcHQtaW4ifSwiMiI6eyJtb2RlIjoib3B0LWluIn0sIjMiOnsibW9kZSI6Im9wdC1pbiJ9LCI0Ijp7Im1vZGUiOiJvcHQtaW4ifSwiNSI6eyJtb2RlIjoib3B0LWluIn0sIjYiOnsibW9kZSI6Im9wdC1pbiJ9LCI3Ijp7Im1vZGUiOiJvcHQtaW4ifX0sInB1cnBvc2VzIjpudWxsLCJfdCI6Im1tN3g4amhvfG02amliMjVvIn0%3D',
        'ry_ry-b13nicij_realytics': 'eyJpZCI6InJ5X0M1QTRERUI4LURERjgtNEE4My1BMzQzLUVFOUExNDJFM0Q3RiIsImNpZCI6bnVsbCwiZXhwIjoxNzY5Nzg3OTE1ODE3LCJjcyI6bnVsbH0%3D',
        '_pin_unauth': 'dWlkPU9XTTFORFUwTlRZdE5UY3hNaTAwTnprMExUaGpOVEV0WkRFNU56aG1OMkUwWkdJMQ',
        'pps': 'pps',
        'access_token': 'i2TiqXcOXVQvlogiiSnC0LPFnfp20XNzRNc7cnmRxfw%3D%3A679cacbe39f78700afc81ab0',
        '_hjSessionUser_4946577': 'eyJpZCI6ImQ1ZTdiY2IwLTgxM2QtNTZhOC04ODVmLWMxYWU2YmFjMGUxMiIsImNyZWF0ZWQiOjE3NDA2NTU3NjI5ODMsImV4aXN0aW5nIjp0cnVlfQ==',
        'chj2': 'chj2',
        'ppsb': 'ppsb',
        'NBVN': '64',
        'listMode': '%7B%22search%22%3A%22list%22%7D',
        'ry_ry-b13nicij_so_realytics': 'eyJpZCI6InJ5X0M1QTRERUI4LURERjgtNEE4My1BMzQzLUVFOUExNDJFM0Q3RiIsImNpZCI6bnVsbCwib3JpZ2luIjp0cnVlLCJyZWYiOm51bGwsImNvbnQiOm51bGwsIm5zIjpmYWxzZSwic2MiOm51bGwsInNwIjpudWxsfQ%3D%3D',
        '_hjSession_4946577': 'eyJpZCI6IjI3MTUwMTdjLTk1ODctNDNhYi1hMGYzLTU1MDM5MjNjMDc3MiIsImMiOjE3NDQyNzk0NjQ2OTIsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowfQ==',
        'webGLBenchmarkScore': '9.99402985074627',
        '__rtbh.lid': '%7B%22eventType%22%3A%22lid%22%2C%22id%22%3A%22KbNvQbc4zAARsDuzrQUQ%22%2C%22expiryDate%22%3A%222026-04-10T10%3A04%3A40.091Z%22%7D',
        '_uetsid': '2e4ab10015f311f0bcc4e938cfac4f1e',
        '_uetvid': '6c2f3aa0f4fe11efba1debd8723035ab',
        'cto_bundle': 'nhPKdl9ldzF0TFVkOVRwOFJ5MEozQVdFJTJGSldtZHVJbFBrc1ZHb3h6TFp1YXJ2enYwWDVHU1A2cHExVkZ6TkcySVFacDFsVEhvTW84VXZ6c3ExdEpNZUJPQWk0eFB0V1N6cnhYZjVFaWZGa1FsbjY0cXdNUWIzJTJGUkhsanZ1UTc1a29HSnFLNlEzYjd0bTRlR3RzJTJCV0JscERFU2clM0QlM0Q',
        'NbPagesVues': '141',
        '__rtbh.uid': '%7B%22eventType%22%3A%22uid%22%2C%22id%22%3A%22679cacXX%22%2C%22expiryDate%22%3A%222026-04-10T10%3A04%3A57.600Z%22%7D',
        'pa_user': '%7B%22id%22%3A%22%22%2C%22category%22%3A%22invite%22%7D',
        'datadome': 'CnQLcOVeQWZQidreuJfZFS10MnaAGuKWCKeShv0yKKMrJVgAqlGnXCDkBc6oQmj~tnX2jGgPpA7sBV5~spmqoXzH0UZKske97yidiT_3im0UjqbAlJy2NkJ3k246X~IS',
    }

    headers = {
        'accept': '*/*',
        'accept-language': 'fr,en-US;q=0.9,en;q=0.8',
        'authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY3OWNhY2JlMzlmNzg3MDBhZmM4MWFiMCIsImlzUmVnaXN0ZXJlZCI6dHJ1ZSwiaWF0IjoxNzQ0Mjc5NTExfQ.ph3hBAe5Uk_WQovMXhEV4icSVw4nF0X23yKfRHNtFd0',
        'dnt': '1',
        'if-none-match': 'W/"3d09d-AzeA4JGg7Lg9FUY2rfXYJA2AbBQ"',
        'priority': 'u=1, i',
        'referer': 'https://www.bienici.com/recherche/achat/gironde-33?page=1',
        'sec-ch-ua': '"Chromium";v="135", "Not-A.Brand";v="8"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
        # 'cookie': 'AB-TESTING=%7B%22relatedAdsPosition%22%3A%22relatedAdsAfterSlideShow%22%7D; i18next=fr; _pcid=%7B%22browserId%22%3A%22m6jib25m4xudrdun%22%2C%22_t%22%3A%22mm7x8ji7%7Cm6jib267%22%7D; _pctx=%7Bu%7DN4IgrgzgpgThIC4B2YA2qA05owMoBcBDfSREQpAeyRCwgEt8oBJAE0RXSwH18yBbfgHYAHgA4AVvSEAffgDYpAIwBM8oSAC%2BQA; _gcl_au=1.1.1754802178.1738251916; _pprv=eyJjb25zZW50Ijp7IjAiOnsibW9kZSI6Im9wdC1pbiJ9LCIxIjp7Im1vZGUiOiJvcHQtaW4ifSwiMiI6eyJtb2RlIjoib3B0LWluIn0sIjMiOnsibW9kZSI6Im9wdC1pbiJ9LCI0Ijp7Im1vZGUiOiJvcHQtaW4ifSwiNSI6eyJtb2RlIjoib3B0LWluIn0sIjYiOnsibW9kZSI6Im9wdC1pbiJ9LCI3Ijp7Im1vZGUiOiJvcHQtaW4ifX0sInB1cnBvc2VzIjpudWxsLCJfdCI6Im1tN3g4amhvfG02amliMjVvIn0%3D; ry_ry-b13nicij_realytics=eyJpZCI6InJ5X0M1QTRERUI4LURERjgtNEE4My1BMzQzLUVFOUExNDJFM0Q3RiIsImNpZCI6bnVsbCwiZXhwIjoxNzY5Nzg3OTE1ODE3LCJjcyI6bnVsbH0%3D; _pin_unauth=dWlkPU9XTTFORFUwTlRZdE5UY3hNaTAwTnprMExUaGpOVEV0WkRFNU56aG1OMkUwWkdJMQ; pps=pps; access_token=i2TiqXcOXVQvlogiiSnC0LPFnfp20XNzRNc7cnmRxfw%3D%3A679cacbe39f78700afc81ab0; _hjSessionUser_4946577=eyJpZCI6ImQ1ZTdiY2IwLTgxM2QtNTZhOC04ODVmLWMxYWU2YmFjMGUxMiIsImNyZWF0ZWQiOjE3NDA2NTU3NjI5ODMsImV4aXN0aW5nIjp0cnVlfQ==; chj2=chj2; ppsb=ppsb; NBVN=64; listMode=%7B%22search%22%3A%22list%22%7D; ry_ry-b13nicij_so_realytics=eyJpZCI6InJ5X0M1QTRERUI4LURERjgtNEE4My1BMzQzLUVFOUExNDJFM0Q3RiIsImNpZCI6bnVsbCwib3JpZ2luIjp0cnVlLCJyZWYiOm51bGwsImNvbnQiOm51bGwsIm5zIjpmYWxzZSwic2MiOm51bGwsInNwIjpudWxsfQ%3D%3D; _hjSession_4946577=eyJpZCI6IjI3MTUwMTdjLTk1ODctNDNhYi1hMGYzLTU1MDM5MjNjMDc3MiIsImMiOjE3NDQyNzk0NjQ2OTIsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowfQ==; webGLBenchmarkScore=9.99402985074627; __rtbh.lid=%7B%22eventType%22%3A%22lid%22%2C%22id%22%3A%22KbNvQbc4zAARsDuzrQUQ%22%2C%22expiryDate%22%3A%222026-04-10T10%3A04%3A40.091Z%22%7D; _uetsid=2e4ab10015f311f0bcc4e938cfac4f1e; _uetvid=6c2f3aa0f4fe11efba1debd8723035ab; cto_bundle=nhPKdl9ldzF0TFVkOVRwOFJ5MEozQVdFJTJGSldtZHVJbFBrc1ZHb3h6TFp1YXJ2enYwWDVHU1A2cHExVkZ6TkcySVFacDFsVEhvTW84VXZ6c3ExdEpNZUJPQWk0eFB0V1N6cnhYZjVFaWZGa1FsbjY0cXdNUWIzJTJGUkhsanZ1UTc1a29HSnFLNlEzYjd0bTRlR3RzJTJCV0JscERFU2clM0QlM0Q; NbPagesVues=141; __rtbh.uid=%7B%22eventType%22%3A%22uid%22%2C%22id%22%3A%22679cacXX%22%2C%22expiryDate%22%3A%222026-04-10T10%3A04%3A57.600Z%22%7D; pa_user=%7B%22id%22%3A%22%22%2C%22category%22%3A%22invite%22%7D; datadome=CnQLcOVeQWZQidreuJfZFS10MnaAGuKWCKeShv0yKKMrJVgAqlGnXCDkBc6oQmj~tnX2jGgPpA7sBV5~spmqoXzH0UZKske97yidiT_3im0UjqbAlJy2NkJ3k246X~IS',
    }   

    params = {
        'filters': '{"size":24,"from":0,"showAllModels":false,"filterType":"buy","propertyType":["house","flat","loft","castle","townhouse"],"page":1,"sortBy":"relevance","sortOrder":"desc","onTheMarket":[true],"zoneIdsByTypes":{"zoneIds":["-7405"]}}',
        'extensionType': 'extendedIfNoResult',
        'enableGoogleStructuredDataAggregates': 'true',
        'leadingCount': '2',
        'access_token': 'i2TiqXcOXVQvlogiiSnC0LPFnfp20XNzRNc7cnmRxfw=:679cacbe39f78700afc81ab0',
        'id': '679cacbe39f78700afc81ab0',
    }

    def get_location_id(self, department):
        url = 'https://res.bienici.com/suggest.json?q=%s' % department
        response = requests.get(url, headers=self.headers)
        assert response.status_code == 200
        location_dict = response.json()[0]
        location_ids_list = location_dict["zoneIds"]
        return location_ids_list 


    def start_requests(self):
        # Générer les URLs pour les départements 1 à 95 donc 1,  96
        for dept in range(1, 96):
            dept_str = f"{dept:02}"  # Format en deux chiffres
            zone = self.get_location_id(dept_str)
            logging.debug(f"Location IDs for department {dept_str}: {zone}")
            self.params['filters'] = f'{{"size":24,"from":0,"showAllModels":false,"filterType":"buy","propertyType":["house","flat","loft","castle","townhouse"],"page":{self.MIN_PAGES},"sortBy":"relevance","sortOrder":"desc","onTheMarket":[true],"zoneIdsByTypes":{{"zoneIds":[{zone[0]}]}}}}'
            response = requests.get('https://www.bienici.com/realEstateAds.json', params=self.params, cookies=self.cookies, headers=self.headers)
            self.parse(response, dept_str)

        # Ajouter les exceptions pour la Corse
        for dept in ['2a', '2b']:
            zone = self.get_location_id(dept)
            self.params['filters'] = f'{{"size":24,"from":0,"showAllModels":false,"filterType":"buy","propertyType":["house","flat","loft","castle","townhouse"],"page":{self.MIN_PAGES},"sortBy":"relevance","sortOrder":"desc","onTheMarket":[true],"zoneIdsByTypes":{{"zoneIds":[{zone[0]}]}}}}'
            response = requests.get('https://www.bienici.com/realEstateAds.json', params=self.params, cookies=self.cookies, headers=self.headers)
            self.parse(response, dept)

    def parse(self, response, department):
        logging.debug(f"Parsing department: {department}")
        try:
            response_json = response.json()
            if not isinstance(response_json, dict):
                logging.error(f"Réponse invalide pour le département {department}: {response_json}")
                return

            if 'total' not in response_json:
                logging.error(f"Département {department} - Pas de données retournées par l'API. Possible blocage.")
                logging.debug(f"Réponse complète: {response_json}")
                return

            total = response_json["total"]
            from_ = response_json.get("from", 0)
            perPage = response_json.get("perPage", self.PAGE_SIZE)
            realEstateAds = response_json.get("realEstateAds", [])
        except ValueError as e:
            logging.error(f"Erreur lors du parsing JSON pour le département {department}: {str(e)}")
            return
        except Exception as e:
            logging.error(f"Erreur inattendue pour le département {department}: {str(e)}")
            return

        logging.debug(f"Total: {total}, From: {from_}, Per Page: {perPage}")
        logging.debug(f"Parsing department: {department}")
        max_pages = self.MAX_PAGES
        if total:
            try:
                max_pages = min(int(total) // perPage, self.MAX_PAGES)
                current_page = (from_ // perPage) + 1
                logging.info(f"Département {department} - Page {current_page}/{max_pages}")
            except (ValueError, IndexError) as e:
                logging.debug(f"Error parsing real estate number from description: {e}")

        # Extraire le nombre total d'annonces en comptant les cartes
        if realEstateAds:
            logging.debug(f"Number of listings on current page: {len(realEstateAds)}")
        
        if not realEstateAds:
            logging.debug(f"No listings found for department {department} on page {response.url}")
            logging.debug(response_json)
            return
        
        self.pages_scraped += 1
        logging.debug(f"Found {len(realEstateAds)} listings on page {response.url}")
        
        for realEstate in realEstateAds:
            # Prix et détails financiers
            price = realEstate.get('price', 0)
            # Extraire toutes les caractéristiques
            features = realEstate

            num_pieces = realEstate.get('roomsQuantity', 0)
            surface_m2 = realEstate.get('surfaceArea', 0)
            num_chambres = realEstate.get('bedroomsQuantity', 0)
            price_per_m2 = realEstate.get('pricePerSquareMeter', 0)

            if isinstance(price, list):
                price = sum(filter(None, price)) / len(price) if price else 0

            if isinstance(price_per_m2, list):
                price_per_m2 = sum(filter(None, price_per_m2)) / len(price_per_m2) if price_per_m2 else 0

            if isinstance(num_chambres, list):
                num_chambres = int(sum(filter(None, num_chambres)) / len(num_chambres)) if num_chambres else 0

            if isinstance(num_pieces, list):
                num_pieces = int(sum(filter(None, num_pieces)) / len(num_pieces)) if num_pieces else 0

            if isinstance(surface_m2, list):
                surface_m2 = sum(filter(None, surface_m2)) / len(surface_m2) if surface_m2 else 0

            if price_per_m2 is None:
                price_per_m2 = price // surface_m2 if surface_m2 > 0 else 0
            logging.debug(f"Price: {price}, Surface: {surface_m2}, Bedrooms: {num_chambres}, Price per m2: {price_per_m2}")

            # Adresse
            address = realEstate.get('district', '').get('name', '')
            city = realEstate.get('city', '')
            postal_code = realEstate.get('postalCode', '')

            # Description
            description = realEstate.get('description', '')

            # Lien vers l'annonce
            listing_url = realEstate.get('id', '')

            # Dictionnaire de traduction des types de biens
            property_type_mapping = {
                'house': 'maison',
                'flat': 'appartement',
                'programme': 'programme',
                'loft': 'loft',
                'castle': 'château',
                'townhouse': 'maison de ville',
            }

            property_type = property_type_mapping.get(realEstate['propertyType'], realEstate['propertyType'])  # Utiliser 'inconnu' si le type n'est pas trouvé

            # Transformation des données pour Spark
            current_time = datetime.now()
            price = float(price) if price is not None else 0
            price_per_m2 = float(price_per_m2) if price_per_m2 is not None else 0
            num_chambres = int(num_chambres) if num_chambres is not None else 0
            num_pieces = int(num_pieces) if num_pieces is not None else 0
            surface_m2 = float(surface_m2) if surface_m2 is not None else 0
            property_data = {
                'department': department,
                'price': price,
                'price_per_m2': price_per_m2,
                'surface_m2': surface_m2,
                'rooms': num_pieces,
                'bedrooms': num_chambres,
                'address': address,
                'city': city,
                'postal_code': postal_code,
                'property_type': property_type,
                'listing_url': listing_url,
                'features': features,
                'description': description,
                'first_seen_at': current_time,  # Date de première découverte
                'last_seen_at': current_time,   # Date de dernière vue
                'last_updated_at': current_time, # Date de dernière modification
                'update_count': 1,              # Nombre de mises à jour
                'is_active': True               # Si l'annonce est toujours active
            }
            
            # Vérification des types avant d'ajouter des propriétés
            if property_data['property_type'] != 'programme':
                self.properties.append(property_data)
            else:
                logging.warning(f'Types incohérents trouvés dans: {property_data}')
            
            logging.info(f'Données collectées : {len(self.properties)}')
            # Sauvegarde par lots de 1000 propriétés pour optimiser Spark
            # ou si un shutdown a été demandé
            if len(self.properties) >= 1000 or self._shutdown_requested:
                if self.properties:
                    logging.info('Création du DataFrame Spark...')
                    df = self.spark.createDataFrame(self.properties)
                    self.save_properties()
                self.properties = []
                if self._shutdown_requested:
                    self.save_stats()
                    logging.debug("Saved all remaining data. Shutting down...")
                    return

        # Gérer la pagination en utilisant un paramètre de requête
        current_page = (from_ // perPage) + 1
        if current_page < max_pages:
            next_page = current_page + 1
            next_from = current_page * perPage
            logging.info(f"Département {department} - Passage à la page {next_page}/{max_pages}")
            zone = self.get_location_id(department)
            self.params['filters'] = f'{{"size":{perPage},"from":{next_from},"showAllModels":false,"filterType":"buy","propertyType":["house","flat","loft","castle","townhouse"],"page":{next_page},"sortBy":"relevance","sortOrder":"desc","onTheMarket":[true],"zoneIdsByTypes":{{"zoneIds":[{zone[0]}]}}}}'
            response = requests.get('https://www.bienici.com/realEstateAds.json', params=self.params, cookies=self.cookies, headers=self.headers)
            self.parse(response, department)
        else:
            logging.debug(f"Département {department} - Fin de la pagination à la page {current_page}/{max_pages}")
            
    def closed(self, reason):
        """Called when the spider is closed"""
        duration = datetime.now() - self.start_time
        
        # Save any remaining properties
        if self.properties:
            logging.info('Création du DataFrame Spark...')
            df = self.spark.createDataFrame(self.properties)
            self.save_properties()
            self.properties = []
        
        # Log final statistics
        logging.debug(f"\nScraping completed - {reason}")
        logging.debug(f"Total properties scraped: {self.properties_scraped}")
        logging.debug(f"New properties: {self.properties_new}")
        logging.debug(f"Updated properties: {self.properties_updated}")
        logging.debug(f"Total pages scraped: {self.pages_scraped}")
        logging.debug(f"Duration: {duration}")
        logging.debug(f"Average properties per page: {self.properties_scraped / max(1, self.pages_scraped):.2f}")
        logging.debug(f"Average time per property: {duration.total_seconds() / max(1, self.properties_scraped):.2f} seconds")
        
        try:
            # Mark inactive listings
            cutoff_time = datetime.now() - timedelta(days=30)  # Properties not seen in 30 days
            result = self.mongo_collection.update_many(
                {"last_seen_at": {"$lt": cutoff_time}, "is_active": True},
                {"$set": {"is_active": False}}
            )
            logging.debug(f"Marked {result.modified_count} listings as inactive")
            
            # Save final statistics
            stats_doc = {
                'timestamp': datetime.now(),
                'duration_seconds': duration.total_seconds(),
                'total_properties': self.properties_scraped,
                'new_properties': self.properties_new,
                'updated_properties': self.properties_updated,
                'total_pages': self.pages_scraped,
                'properties_per_page': self.properties_scraped / max(1, self.pages_scraped),
                'time_per_property': duration.total_seconds() / max(1, self.properties_scraped),
                'reason': reason
            }
            
            self.mongo_db['scraping_stats'].insert_one(stats_doc)
            logging.debug("Statistics saved to MongoDB")
            
        except Exception as e:
            logging.warning(f"Error in cleanup: {str(e)}")
        finally:
            if self.mongo_client:
                self.mongo_client.close()

        # Remove duplicates in MongoDB
        try:
            result = self.mongo_collection.aggregate([
                {"$group": {
                    "_id": "$listing_url",
                    "doc_id": {"$first": "$_id"},
                    "count": {"$sum": 1}
                }},
                {"$match": {"count": {"$gt": 1}}}
            ])
            
            duplicates_removed = 0
            for doc in result:
                delete_result = self.mongo_collection.delete_many({
                    "listing_url": doc["_id"],
                    "_id": {"$ne": doc["doc_id"]}
                })
                duplicates_removed += delete_result.deleted_count
            
            if duplicates_removed > 0:
                logging.debug(f"Removed {duplicates_removed} duplicate listings from MongoDB")
        except Exception as e:
            logging.warning(f"Error removing duplicates from MongoDB: {str(e)}")