import scrapy
from datetime import datetime
from lincoln_scraper.items import MeetingDocumentItem # Adjusted import path

class CabMinutesSpider(scrapy.Spider):
    name = 'cab_minutes'
    # Domains we are allowed to crawl. Includes the main site and the document hosting site.
    allowed_domains = ['www.codot.gov', 'oitco.hylandcloud.com']
    
    # We're now fetching from two different pages on the codot site: one for minutes, one for packets.
    # This requires using start_requests() instead of the simple start_urls list.
    def start_requests(self):
        # Define the source URLs and what type of documents they generally contain
        sources = [
            {
                'url': 'https://www.codot.gov/programs/aeronautics/colorado-aeronautical-board/cab-meeting-minutes-1',
                'source_type': 'minutes' 
            },
            {
                'url': 'https://www.codot.gov/programs/aeronautics/colorado-aeronautical-board/cab-packets',
                'source_type': 'agenda_packet' 
            }
        ]
        # Loop through our defined sources and create a request for each
        for source in sources:
            yield scrapy.Request(
                url=source['url'],
                callback=self.parse_main_listing_page, # Send the response to our main parsing function
                meta={'source_type': source['source_type']} # Pass the source type along so we know where the links came from
            )

    # This function handles the response from the main codot.gov pages (minutes and packets list pages)
    def parse_main_listing_page(self, response):
        # Get the source type we passed in the meta data
        source_type = response.meta['source_type']
        self.logger.info(f"SUCCESS: Reached and processing main listing page: {response.url} (Source Type: {source_type})")
        
        # Try a few CSS selectors to find the links to the actual documents (hosted on Hyland).
        # The site structure might change, so having a few selectors makes it a bit more robust.
        meeting_links_selectors = response.css('article div[class*="content"] p a, article div.item-list ul li a, article .field--name-body a')
        # If the primary selectors don't find anything, broaden the search within the article tag.
        if not meeting_links_selectors:
            meeting_links_selectors = response.css('article a') 
            # If still nothing, maybe the structure changed drastically? Try finding *any* link as a last resort.
            if not meeting_links_selectors:
                self.logger.warning(f"No meeting links found with primary or article selectors on {response.url}. Trying all links.")
                meeting_links_selectors = response.css('a')
        # If we *still* haven't found any links, something is wrong - log an error and stop processing this page.
        if not meeting_links_selectors:
            self.logger.error(f"CRITICAL: No links found on {response.url} to process as meeting links.")
            return

        # Keep track of the Hyland document URLs we've already decided to visit
        # to avoid requesting the same document multiple times if it's linked more than once.
        processed_meeting_detail_urls = set()
        meeting_links_found_count = 0 # Counter to check if we found any valid date links

        # Iterate through all the link elements we found
        for link_selector in meeting_links_selectors:
            # Extract the visible text of the link and the href (URL)
            link_text_from_codot = link_selector.css('::text').get()
            relative_url = link_selector.attrib.get('href')

            # Skip if the link text or URL is missing, or if it's just an anchor link (#)
            if not link_text_from_codot or not relative_url or relative_url.strip() == '#':
                continue

            # Clean up the link text, often it includes things like " (Workshop)"
            link_text_cleaned_for_date_parsing = link_text_from_codot.strip()
            parsed_date = None
            # Try to extract just the date part for parsing (e.g., remove " (Workshop)")
            date_string_for_parsing = link_text_cleaned_for_date_parsing.split('(')[0].strip()

            # Dates on the site aren't always in the same format, so try a few common ones.
            date_formats_to_try = ["%B %d, %Y", "%b %d, %Y", "%B %Y", "%b. %d, %Y", "%m/%d/%Y"]
            for fmt in date_formats_to_try:
                try:
                    # Attempt to parse the date string using the current format
                    parsed_date = datetime.strptime(date_string_for_parsing, fmt)
                    break # Stop trying formats if we successfully parse one
                except ValueError:
                    continue # Try the next format if this one failed
            
            # If we successfully parsed a date from the link text...
            if parsed_date:
                meeting_links_found_count += 1 # Increment our counter
                # Format the date into the required YYYY-MM-DD format
                formatted_date = parsed_date.strftime("%Y-%m-%d")
                # Construct the full URL to the Hyland document page
                document_hyland_url = response.urljoin(relative_url) 

                # Check if we've already added this Hyland URL to our processing queue
                if document_hyland_url in processed_meeting_detail_urls:
                    self.logger.debug(f"Skipping already queued/processed Hyland URL: {document_hyland_url} from {response.url}")
                    continue # Skip to the next link if we have
                processed_meeting_detail_urls.add(document_hyland_url) # Add the URL to our set so we don't process it again
                
                # Log that we're about to request the Hyland document page
                self.logger.info(f"Yielding request for document (Hyland): Original Link Text='{link_text_from_codot.strip()}', Hyland URL='{document_hyland_url}', Source Type='{source_type}'")
                # Create a new request to fetch the Hyland document page
                yield scrapy.Request(
                    document_hyland_url, # The URL for the Hyland page (might redirect to PdfPop.aspx)
                    callback=self.parse_meeting_document_page, # Send this response to the document parsing function
                    meta={ # Pass data along to the next function
                        'meeting_date_iso': formatted_date, # The parsed and formatted date
                        'original_link_text_from_codot': link_text_from_codot.strip(), # The original text from the link on codot.gov
                        'source_type': source_type # Keep track of whether this came from the minutes or packets page
                    }
                )
        
        # After checking all links, if we didn't find any that looked like dates, log a warning.
        if meeting_links_found_count == 0:
            self.logger.warning(f"No links on {response.url} (Source: {source_type}) were successfully parsed as meeting date links. Please verify selectors and link text formats.")

    # This function handles the response after following a link to the Hyland document page (e.g., PdfPop.aspx)
    def parse_meeting_document_page(self, response):
        # Retrieve the data we passed along in the meta dictionary
        meeting_date_iso = response.meta['meeting_date_iso']
        original_link_text_from_codot = response.meta['original_link_text_from_codot'] 
        source_type = response.meta['source_type'] # 'minutes' or 'agenda_packet'
        # The final URL after any redirects (usually ends in PdfPop.aspx?docid=...)
        document_url = response.url

        self.logger.info(f"Processing document page: URL='{document_url}' for date '{meeting_date_iso}', from link '{original_link_text_from_codot}', Source='{source_type}'")
        
        # Determine the category based on which codot.gov page the link came from.
        # This is a simplification based on the source page, not the document content itself.
        category = "other" # Default category
        if source_type == 'minutes':
            category = "minutes" # If the link was on the minutes page, categorize it as minutes

        # Try to create a slightly more descriptive meeting title than just the date.
        descriptive_meeting_title = "Board Meeting" # Default title
        # Check if the original link text mentioned it was a workshop
        if "(workshop)" in original_link_text_from_codot.lower():
            descriptive_meeting_title = "Board Workshop"

        # Create an item to store the extracted data
        item = MeetingDocumentItem()
        item['date'] = meeting_date_iso
        item['meeting_title'] = descriptive_meeting_title # Use our generated title
        item['category'] = category # Use the category determined by the source page
        item['URL'] = document_url # The final URL of the document
        
        # Log the item we're about to yield
        self.logger.info(f"Yielding item: Date='{item['date']}', Title='{item['meeting_title']}', Category='{item['category']}', URL='{item['URL']}' (Source: {source_type})")
        # Yield the item so Scrapy can process it (e.g., save it to the CSV)
        yield item 