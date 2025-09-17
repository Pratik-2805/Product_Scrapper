# Product Scraper (Django) [DEMO](https://product-scrapper-gjlp.onrender.com/)

A Django 5 app that lets users register/login and Scrape Products Details And Tracks Price, with product pages and an image proxy to safely serve remote images. It fetches the HTML content of the page and extracts all Products details from URLs using BeautifulSoup + Scrappingbee.


## Features

- *User accounts*: Register, login, logout.
- *Product browsing*: Dedicated Scrapped page.
- *Product pages*: product/<id>/ shows product details (migrations include Product and ProductPriceHistory).
- *Admin-ready*: Standard Django admin support.
- *Scraping-ready*: Dependencies for web scraping (requests, beautifulsoup4, ScrappingBee)

## Tech Stack

- *Backend*: Django 5.1
- *Templates*: Django templates in templates/
- *Static*: Bootstrap and jQuery vendored in static/
- *DB*: SQLite by default (db.sqlite3)
- *Scraping*: requests, beautifulsoup4, ScrappingBee
- *ASGI/WGI*: uvicorn, gunicorn

## Getting Started (Windows/PowerShell)

1) Clone and navigate:
git clone <this-repo-url>
cd github_image_scrapper


2) Create and activate a virtual environment:
python -m venv .venv
.venv\Scripts\Activate.ps1


3) Install dependencies:
pip install -r requirements.txt


4) Apply migrations:
python manage.py migrate


6) Create a superuser (optional, for admin):
python manage.py createsuperuser


7) Run the dev server:
python manage.py runserver


Visit:
- App: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

## Notes & Tips
- If User want's to scrape heavy websites like Amazon or Flipkart visit https://www.scrapingbee.com/ create an account and copy API key.
- Add your api key in settings.py last line.
- Go into views and follow the steps given.


