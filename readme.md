Lincoln County Meeting Document Scraper

This project contains a Scrapy spider designed to scrape meeting document information (specifically agendas, minutes, and agenda packets) from the Lincoln County, WI CivicClerk portal API.

Prerequisites

- Python 3.8+
- pip (Python package installer)

Setup

1.  **Extract the project files:**
    Unzip the provided project archive.

2.  **Navigate to the project directory:**
    Open a terminal or command prompt and change into the main project directory (the one containing `scrapy.cfg`).

3.  **Create and activate a virtual environment:**

    On Windows:

        python -m venv venv
        .\venv\Scripts\activate

    On macOS/Linux:

        python3 -m venv venv
        source venv/bin/activate

4.  **Install dependencies:**

    pip install -r requirements.txt

Running the Scraper

1.  Make sure your virtual environment is activated.
2.  Navigate to the project root directory (the one containing `scrapy.cfg`), if you aren't already there.
3.  Run the spider using the following command, which will also specify the output file:

    scrapy crawl lincoln_county -O lincoln_county_documents.csv

Output

The scraper will create a CSV file named `lincoln_county_documents.csv` in the project root directory. This file will contain the scraped data with the following columns:

-   date: The date of the meeting (YYYY-MM-DD).
-   meeting_title: The name of the meeting/event.
-   category: The type of document ('agenda', 'minutes', 'agenda_packet', or 'other').
-   URL: The direct URL to the document file. 