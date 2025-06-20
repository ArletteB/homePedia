from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
import logging
import pymongo
from typing import Dict, List, Any
import os
import uuid
from datetime import timedelta

from config import MONGO_CONFIG

class RealEstateSpider(ABC):
    """Classe de base abstraite pour les spiders immobiliers"""



    def get_checkpoint_location(self):
        checkpoint_base = "/opt/bitnami/spark/work/checkpoint"
        checkpoint_dir = os.path.join(checkpoint_base, str(uuid.uuid4()))
        os.makedirs(checkpoint_dir, exist_ok=True)
        return checkpoint_dir
    
    def __init__(self):
        self.properties = []
        self.properties_scraped = 0
        self.properties_new = 0
        self.properties_updated = 0
        self.pages_scraped = 0
        self.start_time = datetime.now()
        
        # Initialisation MongoDB
        self._init_mongodb()
        
    def _init_mongodb(self):
        """Initialise la connexion MongoDB"""
        logging.info(f"Connecting to MongoDB at {MONGO_CONFIG['host']}:{MONGO_CONFIG['port']}")
        mongo_uri = f"mongodb://{MONGO_CONFIG['user']}:{MONGO_CONFIG['password']}@{MONGO_CONFIG['host']}:{MONGO_CONFIG['port']}/{MONGO_CONFIG['database']}"
        
        try:
            self.mongo_client = pymongo.MongoClient(mongo_uri)
            self.mongo_db = self.mongo_client[MONGO_CONFIG['database']]
            self.mongo_collection = self.mongo_db['real_estate']
            logging.info("Successfully connected to MongoDB")
            
            # Create unique index on listing_url if it doesn't exist
            self.mongo_collection.create_index("listing_url", unique=True)
            logging.info("Created unique index on listing_url in MongoDB")
        except Exception as e:
            logging.error(f"Error initializing MongoDB: {str(e)}")
            raise
    
    def save_properties(self):
        """Sauvegarde les propriétés dans MongoDB"""
        if not self.properties:
            return
            
        try:
            # Prepare MongoDB bulk operations
            bulk_ops = []
            for prop in self.properties:
                # Convert Decimal to float for MongoDB
                mongo_doc = {key: float(value) if isinstance(value, Decimal) else value 
                           for key, value in prop.items()}
                
                # Define update operation
                filter_doc = {'listing_url': mongo_doc['listing_url']}
                update_doc = {
                    '$set': {
                        'source': self.name,
                        'department': mongo_doc['department'],
                        'price': mongo_doc['price'],
                        'price_per_m2': mongo_doc['price_per_m2'],
                        'surface_m2': mongo_doc['surface_m2'],
                        'rooms': mongo_doc['rooms'],
                        'bedrooms': mongo_doc['bedrooms'],
                        'address': mongo_doc['address'],
                        'city': mongo_doc['city'],
                        'postal_code': mongo_doc['postal_code'],
                        'property_type': mongo_doc['property_type'],
                        'features': mongo_doc['features'],
                        'description': mongo_doc['description'],
                        'last_seen_at': mongo_doc['last_seen_at'],
                        'is_active': True
                    },
                    '$setOnInsert': {
                        'first_seen_at': mongo_doc['first_seen_at']
                    },
                    '$inc': {'update_count': 1}
                }
                
                bulk_ops.append(pymongo.UpdateOne(filter_doc, update_doc, upsert=True))
            
            # Execute bulk write operation
            if bulk_ops:
                result = self.mongo_collection.bulk_write(bulk_ops, ordered=False)
                self.properties_scraped += len(self.properties)
                self.properties_new += result.upserted_count
                self.properties_updated += result.modified_count
                logging.info(f"Batch save complete - Inserted: {result.upserted_count}, Modified: {result.modified_count}, Matched: {result.matched_count}")
                
            # Clear properties after successful save
            self.properties = []
            
        except pymongo.errors.BulkWriteError as bwe:
            logging.error(f"Bulk write error: {bwe.details}")
        except Exception as e:
            logging.error(f"Error in save_properties: {str(e)}")

    def closed(self, reason):
        """Called when the spider is closed"""
        duration = datetime.now() - self.start_time
        
        # Save any remaining properties
        if self.properties:
            self.save_properties()
        
        # Log final statistics
        logging.info(f"\nScraping completed - {reason}")
        logging.info(f"Total properties scraped: {self.properties_scraped}")
        logging.info(f"Total pages scraped: {self.pages_scraped}")
        logging.info(f"Duration: {duration}")
        logging.info(f"Average properties per page: {self.properties_scraped / max(1, self.pages_scraped):.2f}")
        logging.info(f"Average time per property: {duration.total_seconds() / max(1, self.properties_scraped):.2f} seconds")
        
        try:
            # Mark inactive listings
            cutoff_time = datetime.now() - timedelta(days=30)  # Properties not seen in 30 days
            result = self.mongo_collection.update_many(
                {"last_seen_at": {"$lt": cutoff_time}, "is_active": True},
                {"$set": {"is_active": False}}
            )
            logging.info(f"Marked {result.modified_count} listings as inactive")
            
            # Save final statistics
            stats_doc = {
                'timestamp': datetime.now(),
                'duration_seconds': duration.total_seconds(),
                'total_properties': self.properties_scraped,
                'total_pages': self.pages_scraped,
                'properties_per_page': self.properties_scraped / max(1, self.pages_scraped),
                'time_per_property': duration.total_seconds() / max(1, self.properties_scraped),
                'reason': reason
            }
            
            self.mongo_db['scraping_stats'].insert_one(stats_doc)
            logging.info("Statistics saved to MongoDB")
            
        except Exception as e:
            logging.info(f"Error in cleanup: {str(e)}")
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
                logging.info(f"Removed {duplicates_removed} duplicate listings from MongoDB")
        except Exception as e:
            logging.info(f"Error removing duplicates from MongoDB: {str(e)}")
    
    @abstractmethod
    def start_requests(self):
        """Point d'entrée pour le scraping"""
        pass
        
    @abstractmethod
    def parse(self, response) -> Dict[str, Any]:
        """Parse une annonce immobilière"""
        pass
    
    # @abstractmethod
    # def get_next_page_url(self, response) -> str:
    #     """Récupère l'URL de la page suivante"""
    #     pass
