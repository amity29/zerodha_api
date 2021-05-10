# zerodha_api

[![Python Version](https://img.shields.io/badge/python-3.8-brightgreen.svg)](https://python.org)
[![Django Version](https://img.shields.io/badge/django-2.0.20-brightgreen.svg)](https://djangoproject.com)
[![Redis Server](https://img.shields.io/badge/redis-server-brightgreen.svg)](https://redis.io/)

## Running the Project Locally
First, clone the repository to your local machine:

```bash
git clone https://github.com/amity29/zerodha_api.git
```

Install the requirements:

```bash
pip install -r requirements.txt
```


Create .env file in the settings.py directory

Set up following environment variable:

```
    SECRET_KEY =
    DEBUG =
    URL =
    REDIS_HOST =
    REDIS_PORT =
    REDIS_PASSWORD =
    CHROMEDRIVER_PATH =
```


Finally, run the development server:

```bash
python manage.py runserver
```

The API endpoints will be available at **127.0.0.1:8000** by default.

## API endpoints details

#### Scrape data
```
    http://{server}:{port}/scrape
```
This endpoint will start the Scrapping in the background using thread and store the data in redis db.
You can also run the scraping for a specific date by providing a optional query parameter **date** with the url
```
    http://{server}:{port}/scrape?date={YYYY-MM-DD}
```
    
#### List Result
```
    http://{server}:{port}/list
```
This endpoint will serve the data stored in redis db in the JSON format.
You can also search for a specific name by providing a optional query parameter **search** with the url
```
    http://{server}:{port}/list?search={name}
```

#### Delete Data
```
    http://{server}:{port}/delete
```
This endpoint will delete all the scraped data from redis db.