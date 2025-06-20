import os
from datetime import datetime, timedelta
from urllib.parse import urljoin
import logging
from spiders.base_spider import RealEstateSpider

import pymongo
import scrapy

# Configuration du logger
# logging.basicConfig(level=logging.DEBUG)

# Désactiver les logs de debug MongoDB
logging.getLogger('pymongo').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('pyspark').setLevel(logging.WARNING)
from pyspark.sql import SparkSession
from pyspark.conf import SparkConf
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DecimalType, TimestampType, ArrayType, DoubleType
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.linkextractors import LinkExtractor
from scrapy_fake_useragent.middleware import RandomUserAgentMiddleware
from decimal import Decimal
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

def convert_to_decimal(value, as_decimal=True):
    """Convertit une valeur en Decimal ou float selon le besoin"""
    if value is None:
        return None
    if isinstance(value, str):
        # Remove currency symbols, spaces, and other special characters
        value = value.replace('€', '').replace('/m²', '').replace(' ', '').replace('\xa0', '').strip()
        # Handle comma as decimal separator
        value = value.replace(',', '.')
    if not value:
        return None
    try:
        return Decimal(str(value)) if as_decimal else float(str(value))
    except (ValueError, decimal.InvalidOperation):
        logging.warning(f"Could not convert value '{value}' to numeric type")
        return None

class SeLogerSpider(RealEstateSpider, scrapy.Spider):
    name = "seloger_spider"
    allowed_domains = ["seloger.com"]
    MIN_PAGES = int(os.getenv('MIN_PAGES', 1))
    MAX_PAGES = int(os.getenv('MAX_PAGES', 100))
    PAGE_SIZE = int(os.getenv('PAGE_SIZE', 25))
    
    # Track progress
    properties_scraped = 0
    properties_new = 0
    properties_updated = 0
    pages_scraped = 0
    checkpoint_location = None
    start_time = None
    _shutdown_requested = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        signal.signal(signal.SIGINT, self._handle_sigint)

        # Initialiser la session Spark
        self.logger.info('Initialisation de la session Spark...')
        self.checkpoint_location = self.get_checkpoint_location()
        # Configuration de la session Spark
        conf = SparkConf() \
            .setAppName("SeLogerScraper") \
            .setMaster(os.environ.get("SPARK_MASTER", "local[*]")) \
            .set("spark.driver.memory", "2g") \
            .set("spark.executor.memory", "2g") \
            .set("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.2.1")

        self.spark = SparkSession.builder \
            .config(conf=conf) \
            .getOrCreate()

        self.logger.info("Spark session created successfully.")
        self.properties = []

    def _handle_sigint(self, signum, frame):
        self.logger.info("Received SIGINT, saving remaining properties and stats...")
        self._shutdown_requested = True
        if self.properties:
            self.save_properties()
        self.save_stats()
        self.logger.info("Saved all remaining data. Shutting down...")
        sys.exit(0)

    custom_settings = {
        'COOKIES_ENABLED': True,
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 1,
        'DEFAULT_REQUEST_HEADERS': {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'fr,en-US;q=0.9,en;q=0.8',
            'cache-control': 'max-age=0',
            'dnt': '1',
            'priority': 'u=0, i',
            'sec-ch-device-memory': '8',
            'sec-ch-ua': '"Chromium";v="133", "Not(A:Brand";v="99"',
            'sec-ch-ua-arch': '"arm"',
            'sec-ch-ua-full-version-list': '"Chromium";v="133.0.6943.142", "Not(A:Brand";v="99.0.0.0"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'
        },
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'scrapy_fake_useragent.middleware.RandomUserAgentMiddleware': None,
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,
        },
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [403, 429, 500, 502, 503, 504]
    }

    # Cookies from the working curl request
    #   -b '_gcl_au=1.1.2100235762.1738314672; __gsas=ID=c73e2d30d709ef36:T=1738314671:RT=1738314671:S=ALNI_MYUZBTOHodSF0uQM0OjzWG2AdZwOw; _ga=GA1.2.1264464634.1738314672; _ta=fr~1~1c27cd7cdaf3330364ddfd6a094df6ea; ep-authorization=isDisconnected; visitId=1740655135608-104823386; _lr_env_src_ats=false; _hjSessionUser_736989=eyJpZCI6IjYxZTc4OGMyLTE1MDctNTJkMi05MzdkLTkzMmE1Y2QwZTY5YiIsImNyZWF0ZWQiOjE3MzgzMTQ2NzIyMTAsImV4aXN0aW5nIjp0cnVlfQ==; ry_ry-s3oa268o_realytics=eyJpZCI6InJ5X0MwQjcwMjAwLTQ5QTUtNEJGNS04RkFBLUQ3RUZGNzlFREY5NiIsImNpZCI6bnVsbCwiZXhwIjoxNzcyMTkxMTI3NTU4LCJjcyI6MX0%3D; realytics=1; sl-pdd_LD_UserId=29e35b87-07ec-49ef-bfbe-4fdb6b2ef7ff; _lr_sampling_rate=0; _hjDonePolls=1560252; __gtm_referrer=https%3A%2F%2Farc.net%2F; _tac=false~arc|not-available; _ga_MC53H9VE57=deleted; _gid=GA1.2.1759650436.1741539339; page_viewed_rent=1; ry_ry-s3oa268o_so_realytics=eyJpZCI6InJ5X0MwQjcwMjAwLTQ5QTUtNEJGNS04RkFBLUQ3RUZGNzlFREY5NiIsImNpZCI6bnVsbCwib3JpZ2luIjp0cnVlLCJyZWYiOm51bGwsImNvbnQiOm51bGwsIm5zIjpmYWxzZSwic2MiOm51bGwsInNwIjoiZ2EifQ%3D%3D; _lr_retry_request=true; _tas=ke1v5z0lf6; _gat_tracker_pageview=1; _hjSession_736989=eyJpZCI6IjI3NTVkMzRmLTA3OGItNDJmYy1iYzY1LTM3ZmEyNDc5M2IyOCIsImMiOjE3NDE1NjE5NDU2MDksInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowfQ==; _gat_tracker_ecommerce=1; _ga_MC53H9VE57=GS1.1.1741557654.21.1.1741561955.42.0.0; page_viewed_buy=138; __rtbh.lid=%7B%22eventType%22%3A%22lid%22%2C%22id%22%3A%22MZXr8NZB6Oi59Fyribji%22%2C%22expiryDate%22%3A%222026-03-09T23%3A12%3A35.939Z%22%7D; __rtbh.uid=%7B%22eventType%22%3A%22uid%22%2C%22id%22%3A%22unknown%22%2C%22expiryDate%22%3A%222026-03-09T23%3A12%3A35.943Z%22%7D; _uetsid=4d3cb510fd0711efa5cf1bf0c290bf2e|d4q39y|2|fu2|0|1894; cto_bundle=UfUPPl9LUUhhVHB5VmNyWEphQTlIWk5VRW1LSHd4RjV0RzMlMkZqd2lJQVJJeFBsQklnRHZCUlZuaG5ORVVGWGZBMUJ5M1hkSWV6MGtCd1pSSnBQRmY1ckgyV3AwWUpLTG9Nd0xtQzJXMTlLd0JsNWZ4UEVnb1olMkIlMkYlMkIzUWtCWEpQMHJ4N3dmbEEyWXQzODBnOUFKN3dqYnBlN1psQSUzRCUzRA; cto_bidid=NacFb195JTJCJTJCWG1FVlU3d0R0WWZpMGpwRU5GY3FyNFFuU2hrQWUlMkZlbyUyRnE3VWNXUmJHTUNDOEI0NkslMkZvYU1nak1YNmc3cVpUN2s4aHBQREl4dEF2bno3cW96R2dQbVh1U2JSWXF0aDlBYzQ0dW8lMkZLQSUzRA; datadome=km~COo9XKPcCCWODBxm98HcHScfwEz_qdx6mLDxn2F7UpaDV6PtOJKACN0hu0smXA609QPQPE3Z_l0P9J5BSPmxpHsCXaubO7s7c9F57kt_2Ah8BBBqslQ2egs2dz~mN; _uetvid=3f194f00a82111efa25689b2a3bde22d|1ih0ll6|1741561956870|31|1|bat.bing.com/p/insights/c/u; _dd_s=logs=0&expire=1741562844525&rum=0' \

    cookies = {
        '__gtm_referrer': 'https://www.google.com/',
        '_gcl_au': '1.1.2100235762.1738314672',
        '__gsas': 'ID=c73e2d30d709ef36:T=1738314671:RT=1738314671:S=ALNI_MYUZBTOHodSF0uQM0OjzWG2AdZwOw',
        '_ga': 'GA1.2.1264464634.1738314672',
        '_ta': 'fr~1~1c27cd7cdaf3330364ddfd6a094df6ea',
        'ep-authorization': 'isDisconnected',
        'visitId': '1740655135608-104823386',
        '_lr_env_src_ats': 'false',
        '_hjSessionUser_736989': 'eyJpZCI6IjYxZTc4OGMyLTE1MDctNTJkMi05MzdkLTkzMmE1Y2QwZTY5YiIsImNyZWF0ZWQiOjE3MzgzMTQ2NzIyMTAsImV4aXN0aW5nIjp0cnVlfQ==',
        'ry_ry-s3oa268o_realytics': 'eyJpZCI6InJ5X0MwQjcwMjAwLTQ5QTUtNEJGNS04RkFBLUQ3RUZGNzlFREY5NiIsImNpZCI6bnVsbCwiZXhwIjoxNzcyMTkxMTI3NTU4LCJjcyI6MX0%3D',
        'realytics': '1',
        'sl-pdd_LD_UserId': '29e35b87-07ec-49ef-bfbe-4fdb6b2ef7ff',
        '_lr_sampling_rate': '0',
        '_hjDonePolls': '1560252',
        '__gtm_referrer': 'https%3A%2F%2Farc.net%2F',
        '_tac': 'false~arc|not-available',
        '_ga_MC53H9VE57': 'deleted',
        '_gid': 'GA1.2.1759650436.1741539339',
        'page_viewed_rent': '1',
        'ry_ry-s3oa268o_so_realytics': 'eyJpZCI6InJ5X0MwQjcwMjAwLTQ5QTUtNEJGNS04RkFBLUQ3RUZGNzlFREY5NiIsImNpZCI6bnVsbCwib3JpZ2luIjp0cnVlLCJyZWYiOm51bGwsImNvbnQiOm51bGwsIm5zIjpmYWxzZSwic2MiOm51bGwsInNwIjoiZ2EifQ%3D%3D',
        '_lr_retry_request': 'true',
        '_tas': 'ke1v5z0lf6',
        '_gat_tracker_pageview': '1',
        '_hjSession_736989': 'eyJpZCI6IjI3NTVkMzRmLTA3OGItNDJmYy1iYzY1LTM3ZmEyNDc5M2IyOCIsImMiOjE3NDE1NjE5NDU2MDksInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowfQ==',
        '_gat_tracker_ecommerce': '1',
        '_ga_MC53H9VE57': 'GS1.1.1741557654.21.1.1741561955.42.0.0',
        'page_viewed_buy': '138',
        '__rtbh.lid': '%7B%22eventType%22%3A%22lid%22%2C%22id%22%3A%22MZXr8NZB6Oi59Fyribji%22%2C%22expiryDate%22%3A%222026-03-09T23%3A12%3A35.939Z%22%7D',
        '__rtbh.uid': '%7B%22eventType%22%3A%22uid%22%2C%22id%22%3A%22unknown%22%2C%22expiryDate%22%3A%222026-03-09T23%3A12%3A35.943Z%22%7D',
        '_uetsid': '4d3cb510fd0711efa5cf1bf0c290bf2e|d4q39y|2|fu2|0|1894',
        'cto_bundle': 'UfUPPl9LUUhhVHB5VmNyWEphQTlIWk5VRW1LSHd4RjV0RzMlMkZqd2lJQVJJeFBsQklnRHZCUlZuaG5ORVVGWGZBMUJ5M1hkSWV6MGtCd1pSSnBQRmY1ckgyV3AwWUpLTG9Nd0xtQzJXMTlLd0JsNWZ4UEVnb1olMkIlMkYlMkIzUWtCWEpQMHJ4N3dmbEEyWXQzODBnOUFKN3dqYnBlN1psQSUzRCUzRA',
        'cto_bidid': 'NacFb195JTJCJTJCWG1FVlU3d0R0WWZpMGpwRU5GY3FyNFFuU2hrQWUlMkZlbyUyRnE3VWNXUmJHTUNDOEI0NkslMkZvYU1nak1YNmc3cVpUN2s4aHBQREl4dEF2bno3cW96R2dQbVh1U2JSWXF0aDlBYzQ0dW8lMkZLQSUzRA',
        'datadome': 'km~COo9XKPcCCWODBxm98HcHScfwEz_qdx6mLDxn2F7UpaDV6PtOJKACN0hu0smXA609QPQPE3Z_l0P9J5BSPmxpHsCXaubO7s7c9F57kt_2Ah8BBBqslQ2egs2dz~mN',
        '_uetvid': '3f194f00a82111efa25689b2a3bde22d|1ih0ll6|1741561956870|31|1|bat.bing.com/p/insights/c/u',
        '_dd_s': 'logs=0&expire=1741562844525&rum=0'
    }

    def start_requests(self):
        # Générer les URLs pour les départements 1 à 95
        for dept in range(1, 96):
            dept_str = f"{dept:02}"  # Format en deux chiffres
            url = f'https://www.seloger.com/immobilier/achat/{dept_str}/?LISTING-LISTpg={self.MIN_PAGES}'
            yield scrapy.Request(url=url, dont_filter=True, cookies=self.cookies, callback=self.parse, meta={'department': dept_str, 'dont_redirect': True, 'handle_httpstatus_list': [403, 404, 429, 500, 502, 503, 504]})

        # Ajouter les exceptions pour la Corse
        for dept in ['2a', '2b']:
            url = f'https://www.seloger.com/immobilier/achat/{dept}/?LISTING-LISTpg={self.MIN_PAGES}'
            yield scrapy.Request(url=url, dont_filter=True, cookies=self.cookies, callback=self.parse, meta={'department': dept, 'dont_redirect': True, 'handle_httpstatus_list': [403, 404, 429, 500, 502, 503, 504]})
        
    def closed(self, reason):
        """Called when the spider is closed"""
        duration = datetime.now() - self.start_time
        logging.debug(f"Spider closed: {reason}")
        logging.debug(f"Total properties scraped: {self.properties_scraped}")
        logging.debug(f"Total pages scraped: {self.pages_scraped}")
        logging.debug(f"Duration: {duration}")
        logging.debug(f"Average properties per page: {self.properties_scraped / max(1, self.pages_scraped):.2f}")
        logging.debug(f"Average time per property: {duration.total_seconds() / max(1, self.properties_scraped):.2f} seconds")
        
        if self.mongo_client:
            self.mongo_client.close()
    
    def parse(self, response):
        department = response.meta['department']
        description = response.css('meta[name="description"]::attr(content)').get()
        logging.debug(f"Parsing department: {department}")
        max_pages = self.MAX_PAGES
        if description:
            try:
                real_estate_number = ''.join(c for c in description.split(' ')[0] if c.isdigit())
                max_pages = min(int(real_estate_number) // self.PAGE_SIZE + 1, self.MAX_PAGES)
            except (ValueError, IndexError) as e:
                logging.debug(f"Error parsing real estate number from description: {e}")

        # Extraire le nombre total d'annonces en comptant les cartes
        listings = response.css('div[data-testid="serp-core-classified-card-testid"]')
        if listings:
            logging.debug(f"Number of listings on current page: {len(listings)}")
        
        if not listings:
            logging.debug(f"No listings found for department {department} on page {response.url}")
            return
        
        self.pages_scraped += 1
        logging.debug(f"Found {len(listings)} listings on page {response.url}")
        
        for listing in listings:
            # Prix et détails financiers
            price_text = listing.css('div[data-testid="cardmfe-price-testid"]::text').get()
            price = int(''.join(c for c in price_text if c.isdigit())) if price_text else None
            
            # Extraire toutes les caractéristiques
            features_list = listing.css('div[data-testid="cardmfe-keyfacts-testid"] div::text').getall()

            features = [f for f in features_list if f != '·']

            num_pieces = next((int(f.split()[0]) for f in features if 'pièce' in f and f.split()[0].isdigit()), None)
            surface_m2 = next((float(f.split()[0].replace(',', '.')) for f in features if 'm²' in f and 'terrain' not in f.lower() and f.split()[0].replace(',', '.').replace('.', '').isdigit()), None)
            num_chambres = next((int(f.split()[0]) for f in features if 'chambre' in f and f.split()[0].isdigit()), None)
            price_per_m2 = price // surface_m2 if surface_m2 else None

            # Adresse
            address = listing.css('div[data-testid="cardmfe-description-box-address"]::text').get()
            city = address.split('(')[0].strip() if address else None
            postal_code = address.split('(')[1].replace(')', '').strip() if address and '(' in address else None

            # Description
            description = listing.css('div[data-testid="cardmfe-description-text-test-id"] div::text').getall()
            description = ''.join(description).strip()

            # Lien vers l'annonce
            listing_url = listing.css('a[data-testid="card-mfe-covering-link-testid"]::attr(href)').get()

            # Liste de mots-clés pour détecter le type de bien
            property_keywords = ["maison", "appartement", "terrain", "studio", "villa", "loft"]

            # Récupérer le texte de la description
            description_text = ' '.join(listing.css('div[data-testid="cardmfe-description-box-text-test-id"] div::text').getall()).lower()

            # Initialiser le type de bien à None
            property_type = None

            # Vérifier les mots-clés dans le texte de la description
            for keyword in property_keywords:
                if keyword in description_text:
                    property_type = keyword.capitalize()  # Capitaliser le mot trouvé
                    break

            # Transformation des données pour Spark
            current_time = datetime.now()
            property_data = {
                'department': department,
                'price': convert_to_decimal(price, as_decimal=True),
                'price_per_m2': convert_to_decimal(price_per_m2, as_decimal=True),
                'surface_m2': convert_to_decimal(surface_m2, as_decimal=False) if surface_m2 else None,
                'rooms': convert_to_decimal(num_pieces, as_decimal=False) if num_pieces else None,
                'bedrooms': convert_to_decimal(num_chambres, as_decimal=False) if num_chambres else None,
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
            
            self.properties.append(property_data)
            
            # Sauvegarde par lots de 1000 propriétés pour optimiser Spark
            # ou si un shutdown a été demandé
            if len(self.properties) >= 1000 or self._shutdown_requested:
                if len(self.properties) > 0:
                    logging.info('Création du DataFrame Spark...')
                    df = self.spark.createDataFrame(self.properties)
                    self.save_properties()
                self.properties = []
                if self._shutdown_requested:
                    self.save_stats()
                    logging.debug("Saved all remaining data. Shutting down...")
                    return

        # Gérer la pagination en utilisant un paramètre de requête
        current_page = int(response.url.split('pg=')[1])
        if current_page < max_pages:
            next_page = current_page + 1
            next_page_url = response.url.replace(f'pg={current_page}', f'pg={next_page}')
            logging.debug(f"Moving to page {next_page} of {max_pages}")
            yield scrapy.Request(
                url=next_page_url,
                callback=self.parse,
                cookies=self.cookies,
                dont_filter=True,
                meta={
                    'dont_redirect': True,
                    'handle_httpstatus_list': [403, 404, 429, 500, 502, 503, 504],
                    'department': department
                }
            )
        else:
            logging.debug(f"Reached maximum number of pages ({max_pages}). Stopping.")
            
    def closed(self, reason):
        """Called when the spider is closed"""
        duration = datetime.now() - self.start_time
        
        # Save any remaining properties
        if self.properties:
            if len(self.properties) > 0:
                logging.info('Création du DataFrame Spark...')
                df = self.spark.createDataFrame(self.properties)
                self.save_properties()
        
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