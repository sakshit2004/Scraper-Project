import scrapy

class MeetingDocumentItem(scrapy.Item):
    date = scrapy.Field()
    meeting_title = scrapy.Field()
    category = scrapy.Field()
    URL = scrapy.Field()