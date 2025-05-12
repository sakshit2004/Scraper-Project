import scrapy
import json
from datetime import datetime, timedelta 

class LincolnCountySpider(scrapy.Spider):
    name = 'lincoln_county'
    allowed_domains = ['lincolncowi.api.civicclerk.com', 'lincolncowi.portal.civicclerk.com']
    # The CivicClerk API endpoint for accessing event (meeting) data.
    api_base_url = 'https://lincolncowi.api.civicclerk.com/v1/Events'
    # The base URL for constructing direct links to document files.
    portal_base_url = 'https://lincolncowi.portal.civicclerk.com'
    
    # Track processed pages to limit the scrape as per requirements.
    page_count = 0
    # Requirement: Only scrape the first 2 pages of results.
    max_pages = 2

    # Spider-specific settings override global settings.py
    # Using FEEDS here is simpler than a custom pipeline for basic CSV output.
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'LOG_LEVEL': 'INFO',
        # FEEDS removed, will be handled globally in settings.py
    }

    def start_requests(self):
        # Instead of scraping the static meeting page, we query the API directly.
        # To make the scraped data somewhat relevant, we create a dynamic date window 
        # around the current time, rather than fetching *all* historical/future data.
        today_utc = datetime.utcnow()

        # Define the window: e.g., 15 days back, 45 days forward. 
        # This is arbitrary but ensures we get some recent data.
        start_date_limit_obj = today_utc - timedelta(days=15) 
        end_date_limit_obj = today_utc + timedelta(days=45) 

        # Format dates into the ISO 8601 format required by the OData API filter.
        filter_start_date_str = start_date_limit_obj.strftime('%Y-%m-%dT00:00:00Z')
        # Use 23:59:59 to ensure the end date is inclusive.
        filter_end_date_str = end_date_limit_obj.strftime('%Y-%m-%dT23:59:59Z') 

        self.logger.info(f"Calculated dynamic date window for filtering: START = {filter_start_date_str}, END = {filter_end_date_str}")

        # Construct the OData $filter query parameter. 
        # %20 is URL encoding for space, ge = >=, le = <=.
        odata_filter = (
            f"startDateTime%20ge%20{filter_start_date_str}"
            f"%20and%20startDateTime%20le%20{filter_end_date_str}"
        )
        
        # Construct the full API URL with filtering and sorting.
        # Sorting ensures consistent pagination if needed later.
        url = f"{self.api_base_url}?$filter={odata_filter}&$orderby=startDateTime%20asc,%20eventName%20asc"
        
        self.logger.info(f"Starting scrape for DYNAMIC date range ({self.max_pages} pages max) with URL: {url}")

        # Set headers to mimic a browser request, important for some APIs.
        headers = {
            'Accept': 'application/json', # We expect JSON response from the API
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': self.portal_base_url, # Often needed for CORS
            'Referer': self.portal_base_url + '/', # Often needed for context
        }
        yield scrapy.Request(url=url, headers=headers, callback=self.parse)

    def parse(self, response):
        self.page_count += 1
        self.logger.info(f"Parsing page {self.page_count}: {response.url}")

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse JSON from {response.url}. Response body: {response.text[:500]}")
            return
        
        # API response structure has the list of events under the 'value' key.
        events = data.get('value', [])
        if not events:
            self.logger.info(f"No events found on page {self.page_count} for URL: {response.url} (within the dynamically filtered date range).")

        for event in events:
            # Basic data validation and extraction for each meeting event.
            try:
                meeting_date_iso = event.get('startDateTime')
                if not meeting_date_iso:
                    self.logger.warning(f"Event missing 'startDateTime'. Event data: {event}")
                    continue # Skip event if essential date is missing
                # Convert ISO date string to datetime object, then format as required.
                meeting_date_obj = datetime.strptime(meeting_date_iso, '%Y-%m-%dT%H:%M:%SZ')
                meeting_date_str = meeting_date_obj.strftime('%Y-%m-%d')
            except ValueError:
                self.logger.error(f"Could not parse date: {meeting_date_iso} for event {event.get('eventName')}")
                continue

            meeting_title = event.get('eventName', 'N/A')
            event_id = event.get('id')

            if not event_id:
                self.logger.warning(f"Event '{meeting_title}' on {meeting_date_str} is missing an 'id'. Skipping its files.")
                continue
            
            # Events can have multiple associated files.
            published_files = event.get('publishedFiles', [])
            if not published_files:
                self.logger.debug(f"No published files for event '{meeting_title}' (ID: {event_id}) on {meeting_date_str}.")

            # Process each file associated with the meeting.
            for file_info in published_files:
                # The API provides a 'type' field (e.g., 'Agenda', 'Minutes').
                api_file_type = file_info.get('type', '') 
                file_type_name_lower = api_file_type.lower()
                
                # File ID is needed to construct the download URL.
                file_id = file_info.get('fileId') 

                if not file_id or file_id == 0: 
                    self.logger.warning(
                        f"File for event '{meeting_title}' (ID: {event_id}) is missing a valid 'fileId' (found: {file_id}). "
                        f"Original API type: '{api_file_type}'. Skipping this file."
                    )
                    continue

                # Map the API file type to the required categories.
                # Default to 'other' and be specific about other categories.
                category = 'other'  
                if 'agenda' in file_type_name_lower and 'packet' in file_type_name_lower:
                    category = 'agenda_packet'
                elif 'agenda' in file_type_name_lower: # Check after agenda_packet
                    category = 'agenda'
                elif 'minutes' in file_type_name_lower:
                    category = 'minutes'
                
                # Optional: Log when a file is categorized as 'other' for potential review.
                if category == 'other' and api_file_type:
                    self.logger.info(
                        f"File with API type '{api_file_type}' for event {event_id}, fileId {file_id} "
                        f"categorized as 'other'."
                    )

                # Construct the direct download URL for the file.
                # NOTE: The path component '/agenda/' seems required based on observed portal URLs,
                # even for minutes/packets. Might need adjustment if the portal structure changes.
                url_path_component = 'agenda'
                                
                file_url = f"{self.portal_base_url}/event/{event_id}/files/{url_path_component}/{file_id}"
                
                # Yield a dictionary matching the desired CSV structure for each document.
                yield {
                    'date': meeting_date_str,
                    'meeting_title': meeting_title,
                    'category': category,
                    'URL': file_url,
                }

        # Pagination logic: Check if we are below the max page limit and if the API provided a next link.
        if self.page_count < self.max_pages: 
            # The API provides the URL for the next page in '@odata.nextLink'.
            next_link = data.get('@odata.nextLink')
            if next_link:
                self.logger.info(f"Following pagination link to: {next_link}")
                # Reuse the headers from the initial request.
                headers = response.request.headers 
                yield scrapy.Request(url=next_link, headers=headers, callback=self.parse)
            else:
                self.logger.info(f"No more pages to scrape (API provided no nextLink or all data within date range fetched before {self.max_pages} pages).")
        else:
            # Stop scraping once the page limit is reached.
            self.logger.info(f"Reached max_pages limit ({self.max_pages}). Stopping pagination.")