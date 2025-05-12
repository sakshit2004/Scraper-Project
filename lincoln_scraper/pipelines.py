import pymongo
import logging

class MongoPipeline:

    def __init__(self, mongo_uri, mongo_db, mongo_collection):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.mongo_collection_name = mongo_collection
        self.client = None
        self.db = None
        self.collection = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DB', 'scrapy_data'), # Default DB
            mongo_collection=crawler.settings.get('MONGO_COLLECTION', 'scraped_documents') # Default collection
        )

    def open_spider(self, spider):
        try:
            self.client = pymongo.MongoClient(self.mongo_uri)
            self.db = self.client[self.mongo_db]
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
            return item # Or raise DropItem
        try:
            # Make sure item is a dict (Scrapy items are dict-like but might need conversion)
            self.collection.insert_one(dict(item))
            logging.debug(f"Item inserted into MongoDB: {item}")
        except Exception as e:
            logging.error(f"Error inserting item into MongoDB: {e}")
            # Decide if you want to drop the item or let it pass
            # from scrapy.exceptions import DropItem
            # raise DropItem(f"Failed to insert item into MongoDB: {item}")
        return item
