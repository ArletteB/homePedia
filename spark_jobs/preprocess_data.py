from pyspark.sql import SparkSession
from pyspark.sql.functions import col, length, regexp_replace, lower, when, to_date
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

# PostgreSQL connection info from .env
POSTGRES_HOST = os.getenv("DB_HOST")
POSTGRES_PORT = os.getenv("DB_PORT")
POSTGRES_DB = os.getenv("DB_NAME")
POSTGRES_USER = os.getenv("DB_USER")
POSTGRES_PASS = os.getenv("DB_PASSWORD")
POSTGRES_TABLE = os.getenv("DB_TABLE")

# MongoDB URI
MONGO_URI = f"mongodb://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASSWORD')}@{os.getenv('MONGO_HOST')}:{os.getenv('MONGO_PORT')}/{os.getenv('MONGO_DB')}.real_estate"

def process_data():
    spark = None
    try:
        # Spark Session Setup
        spark = SparkSession.builder \
            .appName("RealEstate-Mongo-Extraction") \
            .config("spark.mongodb.read.connection.uri", MONGO_URI) \
            .config("spark.driver.memory", "2g") \
            .config("spark.executor.memory", "2g") \
            .config("spark.executor.cores", "1") \
            .config("spark.default.parallelism", "4") \
            .config("spark.sql.shuffle.partitions", "4") \
            .getOrCreate()

        # Extraction Pipeline
        mongo_pipeline = """
        [
          { "$match": {"processed": false} },
          { "$limit": 2000 },
          { "$project": { "_id": 1, "price": 1, "surface_m2": 1, "city": 1, "property_type": 1, "rooms": 1, "scraped_at": 1, "postal_code": 1 } }
        ]
        """

        logging.info("Loading data from MongoDB")
        # Read data from MongoDB
        df = spark.read.format("mongodb") \
            .option("pipeline", mongo_pipeline) \
            .load()

        # Transform Data
        logging.info("Transforming data")
        df_transformed = df.select(
            col("_id").alias("Id"),
            col("price").cast("double").alias("Price"),
            col("surface_m2").cast("double").alias("M2"),
            col("city").alias("City"),
            col("property_type").alias("Name"),
            col("rooms").cast("int").alias("Rooms"),
            col("postal_code").alias("ZipCode"),
            col("scraped_at").alias("Date"),
        )

        # Data Cleaning and Transformation
        df_clean = df_transformed.filter(col("ZipCode").isNotNull()) \
            .withColumn("ZipCode", regexp_replace(col("ZipCode"), "\\s+", "")) \
            .filter((length(col("ZipCode")) == 5) & (col("ZipCode").rlike(r'^\d{5}$'))) \
            .filter((col("Price").isNotNull()) & (col("Price") > 10000) & (col("M2").isNotNull()) & (col("M2") >= 9)) \
            .withColumn("Name", lower(col("Name")))

        # Determine Logement Type
        logement_map = {
            "maison": ["maison", "mas", "chalet", "villa"],
            "appartement": ["appartement", "studio", "duplex", "triplex", "loft"]
        }

        logement_expr = when(col("Name").contains("maison"), "maison")
        for logement_type, keywords in logement_map.items():
            for keyword in keywords:
                logement_expr = logement_expr.when(col("Name").contains(keyword), logement_type)
        logement_expr = logement_expr.otherwise("autre")

        df_clean = df_clean.withColumn("Logement", logement_expr) \
            .filter(col("Logement") != "autre") \
            .withColumn("Rooms", when(col("Name").contains("studio"), 1).otherwise(col("Rooms"))) \
            .withColumn("Date", to_date(col("Date"), "yyyy-MM-dd"))

        # Collect Processed IDs
        processed_ids = [row.Id for row in df_clean.select("Id").collect()]

        # Write to PostgreSQL
        logging.info("Writing data to PostgreSQL")
        jdbc_url = f"jdbc:postgresql://{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
        connection_properties = {
            "user": POSTGRES_USER,
            "password": POSTGRES_PASS,
            "driver": "org.postgresql.Driver"
        }

        df_clean.select("Name", "Price", "M2", "City", "Logement", "Rooms", "Date", "ZipCode").write \
            .option("batchsize", 500) \
            .jdbc(jdbc_url, POSTGRES_TABLE, mode="append", properties=connection_properties)

        # Update MongoDB
        logging.info("Updating MongoDB documents")
        client = MongoClient(MONGO_URI)
        db = client[os.getenv('MONGO_DB')]
        collection = db.real_estate

        collection.update_many(
            {"_id": {"$in": processed_ids}},
            {"$set": {"processed": True}}
        )
        logging.info("Processing complete")

    except Exception as e:
        logging.error(f"An error occurred: {e}")

    finally:
        if spark:
            spark.stop()
            logging.info("Spark session stopped")

if __name__ == "__main__":
    process_data()