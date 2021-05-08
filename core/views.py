from django.shortcuts import render
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
import pickle
# Create your views here.

# http://127.0.0.1:8000/core/scrape
class ScrapeView(APIView):
    def get(self, request):
        res, status = self.scrape()
        return Response(res, status=status)

        # return Response({1:2})

    def scrape(self):
        chromeOptions = webdriver.ChromeOptions()

        download_dir = os.path.join(settings.MEDIA_ROOT, "bse_zip")
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)

        prefs = {"download.default_directory": download_dir}
        chromeOptions.add_experimental_option("prefs", prefs)
        driver = webdriver.Chrome(executable_path=f"{settings.BASE_DIR}/chromedriver", options=chromeOptions)

        url = os.getenv('URL')
        driver.get(url)
        driver.implicitly_wait(30)

        today = timezone.now() - timezone.timedelta(1)

        # day, month, year = map(str, (today.day, today.month, today.year))

        day, month, year = "23", "3", "2021"

        date_selector = Select(driver.find_element_by_id("ContentPlaceHolder1_fdate1"))
        date_selector.select_by_value(day)
        month_selector = Select(driver.find_element_by_id("ContentPlaceHolder1_fmonth1"))
        month_selector.select_by_value(month)
        year_selector = Select(driver.find_element_by_id("ContentPlaceHolder1_fyear1"))
        year_selector.select_by_value(year)

        driver.find_element_by_id("ContentPlaceHolder1_btnSubmit").click()

        is_file_present = not self.is_element_present(By.ID, "ContentPlaceHolder1_lblCurZip", driver)

        print("is_file_present", is_file_present)

        is_file_present = True

        if is_file_present:
            driver.find_element_by_id("ContentPlaceHolder1_btnHylSearBhav").click()
            time.sleep(15)
            driver.quit()
            file_name = self.unzip_file(download_dir)
            self.read_csv(file_name)
            return {"success": True}, 200

        else:
            msg = driver.find_element_by_id("ContentPlaceHolder1_lblCurZip").get_attribute("innerHTML")
            driver.quit()
            return {"success": False, "message": msg}, 404

    def is_element_present(self, how, what, driver):
        try:
            driver.find_element(by=how, value=what)
        except NoSuchElementException:
            return False
        return True

    def unzip_file(self, download_dir):
        list_of_files = glob.glob(download_dir + '/*')
        latest_file = max(list_of_files, key=os.path.getctime)
        zip_ref = zipfile.ZipFile(latest_file)

        unzip_dir = os.path.join(settings.MEDIA_ROOT, "bse_extract")
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        zip_ref.extractall(unzip_dir)
        zip_ref.close()
        return latest_file

    def read_csv(self, file_name):
        df = pd.read_csv(file_name, usecols=['SC_CODE', 'SC_NAME', 'OPEN', 'HIGH', 'LOW', 'CLOSE'])
        df['SC_NAME'] = df['SC_NAME'].str.strip()
        df['SC_NAME'] = df['SC_NAME'].str.lower()
        dict = df.to_dict(orient="records")

        for data in dict:
            redis_db.hset("Bhavcopy", data['SC_NAME'].strip(), json.dumps(data))

        return True


# http://127.0.0.1:8000/core/list
class ListView(APIView):
    def get(self, request):

        # # a = redis_db.hget('Bhavcopy', '*10MFL*')
        # a = redis_db.hscan(name='Bhavcopy', cursor=0, match='10M*', count=1000)
        # print("a",a)
        # return Response({1:2})
        search_key = request.query_params.get('key')
        print("ss", search_key)
        if not search_key:
            data = redis_db.hgetall('Bhavcopy')
        else:
            search_key = search_key.lower()
            data = redis_db.hscan(name='Bhavcopy', cursor=0, match=f'*{search_key}*', count=1000000)[1]

        print(search_key, data)

        new_data = []
        if data:
            # new_data = [{k: json.loads(v)} for k, v in data.items()]
            new_data = [json.loads(v) for k, v in data.items()]

        return Response(new_data)
