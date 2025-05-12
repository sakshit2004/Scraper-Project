# Lincoln County & CO DOT CAB Document Scraper

This project contains Scrapy spiders to scrape meeting documents (minutes, agendas, packets) from two sources:

1.  **Lincoln County, WI:** Utilizes the CivicClerk portal API.
2.  **Colorado Department of Transportation (CDOT) Aeronautics Board (CAB):** Scrapes the official board website.

The scraped data from both spiders is combined and stored in a MongoDB database. A GitHub Actions workflow is configured to run the spiders daily.

## Prerequisites

-   Python 3.9+
-   pip (Python package installer)
-   Access to a MongoDB instance (local or cloud-based like MongoDB Atlas)

## Setup

1.  **Clone the Repository:**
    ```bash
    # Replace with your repository URL
    git clone <your-repository-url>
    cd LincolnScraper
    ```

2.  **Create and Activate Virtual Environment:**
    (Use `python` or `python3` depending on your system setup)

    *   Windows:
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```
    *   macOS/Linux:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure MongoDB Connection (Local Run):**
    *   Edit the `lincoln_scraper/settings.py` file.
    *   Update the `MONGO_URI` setting with your MongoDB connection string (e.g., `mongodb://localhost:27017/`).
    *   Optionally, change `MONGO_DB` and `MONGO_COLLECTION` if desired.

## Running Locally

Ensure your virtual environment is activated and MongoDB is running and accessible.

1.  **Navigate to Project Root:** Make sure you are in the `LincolnScraper` directory (the one containing `scrapy.cfg`).
2.  **Run Spiders:**
    *   To run sequentially using the included batch script (Windows):
        ```bash
        .\run_spiders.bat
        ```
        *(Note: This script assumes default settings in `settings.py`. It doesn't clear the MongoDB collection.)*
    *   To run spiders individually (clears collection if `MONGO_OVERWRITE_COLLECTION=True` in settings):
        ```bash
        # Run Lincoln County spider
        scrapy crawl lincoln_county

        # Run CDOT CAB spider
        scrapy crawl cab_minutes
        ```

## GitHub Actions CI/CD

This repository includes a GitHub Actions workflow (`.github/workflows/scrape_schedule.yml`) configured to:

1.  **Run on a Schedule:** Executes automatically every day at midnight UTC (`0 0 * * *`).
2.  **Run Manually:** Can be triggered manually from the Actions tab in the GitHub repository.
3.  **Scrape Data:** Runs both the `lincoln_county` and `cab_minutes` spiders.
4.  **Overwrite MongoDB:**
    *   The first spider (`lincoln_county`) is run with `MONGO_OVERWRITE_COLLECTION=True`, causing the target MongoDB collection to be **dropped** before inserting new data.
    *   The second spider (`cab_minutes`) runs with `MONGO_OVERWRITE_COLLECTION=False`, appending its data to the now-refreshed collection.
5.  **Use Secrets:** The workflow uses GitHub Actions secrets to connect to MongoDB securely:
    *   `MONGO_URI`: Your MongoDB Atlas connection string (or other publicly accessible URI).
    *   `MONGO_DB`: The target database name.
    *   `MONGO_COLLECTION`: The target collection name.

**Important:** For the GitHub Actions workflow to function, you **must** configure these secrets in your repository settings under "Secrets and variables" > "Actions".

## Output Data Structure

Data from both spiders is stored in the specified MongoDB collection (default: `lincoln_cab_documents` in the `scrapy_data` database). Each document represents a scraped meeting item and has the following structure:

![image](https://github.com/user-attachments/assets/94d6bba9-406f-4d52-8ed2-1da91b24c66d)
![image](https://github.com/user-attachments/assets/26d4d285-0d66-44ff-b228-856a1f6e3922)
