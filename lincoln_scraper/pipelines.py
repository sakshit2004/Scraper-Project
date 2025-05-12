import pymongo
import logging

class MongoPipeline:

    def __init__(self, mongo_uri, mongo_db, mongo_collection, overwrite_collection):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.mongo_collection_name = mongo_collection
        self.overwrite_collection = overwrite_collection
        self.client = None
        self.db = None
        self.collection = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DB', 'scrapy_data'),
            mongo_collection=crawler.settings.get('MONGO_COLLECTION', 'scraped_documents'),
            overwrite_collection=crawler.settings.getbool('MONGO_OVERWRITE_COLLECTION', False)
        )

    def open_spider(self, spider):
        try:
            self.client = pymongo.MongoClient(self.mongo_uri)
            self.db = self.client[self.mongo_db]
            
            if self.overwrite_collection:
                logging.info(f"Overwriting enabled. Dropping collection: {self.mongo_collection_name} in DB: {self.mongo_db}")
                self.db.drop_collection(self.mongo_collection_name)
                self.overwrite_collection = False 

            self.collection = self.db[self.mongo_collection_name]
            logging.info(f"MongoDB connection established. DB: {self.mongo_db}, Collection: {self.mongo_collection_name}")
        except pymongo.errors.ConfigurationError as e:
            logging.error(f"MongoDB configuration error: {e}")
            raise
        except pymongo.errors.ConnectionFailure as e:
            logging.error(f"MongoDB connection failed: {e}")
            raise

    def close_spider(self, spider):
        if self.client:
            self.client.close()
            logging.info("MongoDB connection closed.")

    def process_item(self, item, spider):
        if self.collection is None:
            logging.error("MongoDB collection not available. Item not processed.")
            return item
        try:
            self.collection.insert_one(dict(item))
            logging.debug(f"Item inserted into MongoDB: {item}")
        except Exception as e:
            logging.error(f"Error inserting item into MongoDB: {e}")
        return item
