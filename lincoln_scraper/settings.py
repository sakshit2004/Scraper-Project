import pathlib

BOT_NAME = 'lincoln_scraper'

SPIDER_MODULES = ['lincoln_scraper.spiders']
NEWSPIDER_MODULE = 'lincoln_scraper.spiders'

# It's generally good practice to obey robots.txt, but for scraping specific
# API endpoints like CivicClerk's, which aren't typically disallowed,
# we disable it to ensure we can fetch the required data.
ROBOTSTXT_OBEY = False

DOWNLOAD_DELAY = 1

CONCURRENT_REQUESTS = 16

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'

DEFAULT_REQUEST_HEADERS = {
   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
   'Accept-Language': 'en-US,en;q=0.9',
   'Accept-Encoding': 'gzip, deflate, br',
   'Connection': 'keep-alive',
   'Upgrade-Insecure-Requests': '1',
   'Cache-Control': 'no-cache',
   'Pragma': 'no-cache',
   'Sec-Ch-Ua': '"Chromium";v="120", "Google Chrome";v="120", "Not=A?Brand";v="99"',
   'Sec-Ch-Ua-Mobile': '?0',
   'Sec-Ch-Ua-Platform': '"Windows"',
   'Sec-Fetch-Dest': 'document',
   'Sec-Fetch-Mode': 'navigate',
   'Sec-Fetch-Site': 'none',
   'Sec-Fetch-User': '?1',
   'Referer': 'https://lincolncowi.portal.civicclerk.com/',
}

# FEED_URI removed, using FEEDS dictionary below for more control
# FEED_FORMAT = "csv" # This is implicitly handled by FEEDS format key

# FEEDS = {
#     'lincoln_county_documents.csv': {
#         'format': 'csv',
#         'encoding': 'utf8',
#         'store_empty': False,
#         'fields': ['date', 'meeting_title', 'category', 'URL'],
#         'overwrite': False, # Set to False to append
#     }
# }
# FEED_EXPORT_INCLUDE_HEADERS_LINE = True # Default to writing headers

# MongoDB Settings
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB = "scrapy_data"
MONGO_COLLECTION = "lincoln_cab_documents"
MONGO_OVERWRITE_COLLECTION = False

ITEM_PIPELINES = {
   "lincoln_scraper.pipelines.MongoPipeline": 300,
}

COOKIES_ENABLED = True

RETRY_TIMES = 5

RETRY_HTTP_CODES = [403, 429, 500, 502, 503, 504, 522, 524, 408, 404]

DOWNLOAD_TIMEOUT = 30

LOG_LEVEL = 'DEBUG'

RANDOMIZE_DOWNLOAD_DELAY = True

CONCURRENT_REQUESTS_PER_DOMAIN = 1

CONCURRENT_REQUESTS_PER_IP = 1

HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 0
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = []
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,
    'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': 130,
    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
    'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': 800,
    'scrapy.downloadermiddlewares.defaultheaders.DefaultHeadersMiddleware': 400,
    "lincoln_scraper.middlewares.LincolnScraperDownloaderMiddleware": 543,
}

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = False

AUTOTHROTTLE_DEBUG = False

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

SPIDER_MIDDLEWARES = {
   "lincoln_scraper.middlewares.LincolnScraperSpiderMiddleware": 543,
}
