from rest_framework.response import Response
from rest_framework.views import APIView
from selenium import webdriver
from selenium.webdriver.support.ui import Select
import time
from django.conf import settings
import os
from django.utils import timezone
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
import glob
import zipfile
from zerodha_api.settings import redis_db
import pandas as pd
import json
import threading
from .serializers import DateSerializer
# Create your views here.


# http://127.0.0.1:8000
class TestView(APIView):
    def get(self, request):
        """
        To test the server status
        """
        redis_status = True
        keys = None
        try:
            keys = redis_db.keys()
        except Exception as e:
            redis_status = False

        return Response({
                         "redis_keys": keys,
                         "redis_status": redis_status,
                         "django_server": "Running"
                         })


# http://127.0.0.1:8000/scrape
# http://127.0.0.1:8000/scrape?date=2021-02-04
class ScrapeView(APIView):
    def get(self, request):
        """
        This will trigger the scrapping function in background and
        return response without waiting for the func to be complete.
        """
        s = DateSerializer(data=request.query_params)
        s.is_valid(raise_exception=True)

        date = s.validated_data.get('date', (timezone.now() - timezone.timedelta(1)).date())
        redis_db.delete('Bhavcopy')

        x = threading.Thread(target=self.scrape, args=(date,))
        x.start()

        return Response({
            "message": "Scrape start",
            "scrape_date": str(date),
            "success": True
        }, status=200)

    def scrape(self, date):
        """
        This function will start the scrapping process

        :param date:
        :return: True/False

        """
        day, month, year = map(str, (date.day, date.month, date.year))

        download_dir = os.path.join(settings.MEDIA_ROOT, "bse_zip")
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        chrome_options = webdriver.ChromeOptions()
        if not settings.DEBUG:
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")

        prefs = {"download.default_directory": download_dir}
        chrome_options.add_experimental_option("prefs", prefs)

        print("CHROMEDRIVER_PATH ", os.environ.get("CHROMEDRIVER_PATH"))

        driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), options=chrome_options)

        url = os.getenv('URL')
        driver.get(url)
        driver.implicitly_wait(30)

        date_selector = Select(driver.find_element_by_id("ContentPlaceHolder1_fdate1"))
        date_selector.select_by_value(day)
        month_selector = Select(driver.find_element_by_id("ContentPlaceHolder1_fmonth1"))
        month_selector.select_by_value(month)
        year_selector = Select(driver.find_element_by_id("ContentPlaceHolder1_fyear1"))
        year_selector.select_by_value(year)

        driver.find_element_by_id("ContentPlaceHolder1_btnSubmit").click()

        is_file_present = not self.is_element_present(By.ID, "ContentPlaceHolder1_lblCurZip", driver)

        print("is_file_present ",is_file_present)

        if is_file_present:
            driver.find_element_by_id("ContentPlaceHolder1_btnHylSearBhav").click()
            time.sleep(15)
            driver.quit()
            file_name = self.unzip_file(download_dir)
            self.read_csv(file_name)
            return True

        else:
            msg = driver.find_element_by_id("ContentPlaceHolder1_lblCurZip").get_attribute("innerHTML")
            driver.quit()
            return False

    def is_element_present(self, how, what, driver):
        """
        Helper function to check if element is present in HTML page
        :param how:
        :param what:
        :param driver:
        :return: True/False
        """
        try:
            driver.find_element(by=how, value=what)
        except NoSuchElementException:
            return False
        return True

    def unzip_file(self, download_dir):
        """
        Extract the downloaded zip file
        :param download_dir:
        :return: latest file path
        """
        list_of_files = glob.glob(download_dir + '/*')
        latest_file = max(list_of_files, key=os.path.getctime)
        zip_ref = zipfile.ZipFile(latest_file)

        unzip_dir = os.path.join(settings.MEDIA_ROOT, "bse_extract")
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        zip_ref.extractall(unzip_dir)
        zip_ref.close()
        print("File extraction complete")
        return latest_file

    def read_csv(self, file_name):
        """
        Read the extracted CSV file and load data in redis hash.
        :param file_name:
        :return: True
        """
        df = pd.read_csv(file_name, usecols=['SC_CODE', 'SC_NAME', 'OPEN', 'HIGH', 'LOW', 'CLOSE'])
        df['SC_NAME'] = df['SC_NAME'].str.strip()
        df['SC_NAME'] = df['SC_NAME'].str.lower()
        dict = df.to_dict(orient="records")

        for data in dict:
            redis_db.hset("Bhavcopy", data['SC_NAME'].strip(), json.dumps(data))

        print("Read csv complete")
        return True


# http://127.0.0.1:8000/list
# http://127.0.0.1:8000/list?search=0mmf
class ListView(APIView):
    def get(self, request):
        """
        Return all the Scraped data stored in redis hash in JSON format
        """
        search_key = request.query_params.get('search')
        if not search_key:
            data = redis_db.hgetall('Bhavcopy')
        else:
            search_key = search_key.lower()
            data = redis_db.hscan(name='Bhavcopy', cursor=0, match=f'*{search_key}*', count=1000000)[1]

        new_data = []
        if data:
            new_data = [json.loads(v) for k, v in data.items()]

        return Response(new_data, status=200)


# http://127.0.0.1:8000/delete
class DeleteView(APIView):
    def get(self, request):
        """
        Delete all the store data in redis hash.
        """
        redis_db.delete('Bhavcopy')
        return Response({
            "success": True
        }, status=200)
