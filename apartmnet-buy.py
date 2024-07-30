import requests
import mysql.connector
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
import time
import datetime
import convert_numbers

# Specify the path to the ChromeDriver executable
driver_path = 'C:\\chromedriver-win64\\chromedriver.exe'

# Configure Chrome options for headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")
# chrome_options.add_argument("--disable-gpu")
# chrome_options.add_argument("--window-size=1920x1080")

# Initialize the WebDriver with headless mode
service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Database connection
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="divar"
)
mycursor = mydb.cursor(buffered=True)

mycursor.execute('DELETE FROM buyapartment')
mydb.commit()

presentDate = datetime.datetime.now()
last_post_date = presentDate.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

url = 'https://api.divar.ir/v8/postlist/w/search'

payload = {
  "city_ids": [ 
    "1722", "1721", "1739", "1740","850","1751", "2",
    "1738","1720","1753","1752","774","1754"
  ],
  "pagination_data": {
    "@type": "type.googleapis.com/post_list.PaginationData",
    "page": 1,
    "layer_page": 1,
    "search_uid": "4eb9e537-70f5-4778-94d5-10728e3e4f83"
  },
  "search_data": {
    "form_data": {
      "data": {
        "category": {
          "str": {
            "value": "apartment-sell"
          }
        },
        "sort": {
          "str": {
            "value": "sort_date"
          }
        }
      }
    }
  }
}

try:
    for i in range(20):  # Adjust the range for the number of pages you want to scrape
        payload['pagination_data']['last_post_date'] = last_post_date
        res = requests.post(url, json=payload, headers={"Content-type": "application/json"})
        res_json = res.json()
        last_post_date = res_json['pagination']['data']['last_post_date']
        items = res_json['list_widgets']

        for item in items:
            token = item['data']['action']['payload']['token']
            sql_where = "SELECT token FROM buyapartment WHERE token = %s"
            mycursor.execute(sql_where, (token,))
            token_exist = mycursor.fetchone()

            if not token_exist:
                print('Fetching: https://divar.ir/v/-/' + token)
                driver.get('https://divar.ir/v/-/' + token)
                time.sleep(5)

                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                check = soup.select('.kt-page-title__title--responsive-sized')
                if not check:
                  continue
                
                info = soup.select('tr.kt-group-row__data-row td')
                info2 = soup.select('p.kt-unexpandable-row__value')
                title = soup.select('.kt-page-title__title--responsive-sized')[0].text
                location = soup.select('.kt-page-title__subtitle--responsive-sized')[0].text                            
                
                gheimate_kol = convert_numbers.persian_to_english(info2[0].text.replace(' تومان', '').replace('٬', ''))
                gheimate_har_metr = convert_numbers.persian_to_english(info2[1].text.replace(' تومان', '').replace('٬', ''))                

                if gheimate_kol == '' or gheimate_har_metr == '':
                    continue

                location = location.split(' پیش در ')[1] if ' پیش در ' in location else location

                metraj = convert_numbers.persian_to_english(info[0].text)
                sale_sakht = convert_numbers.persian_to_english(info[1].text)
                otagh = convert_numbers.persian_to_english(info[2].text.replace('بدون اتاق', '0'))
                if len(info) == 8:
                    asansor = '0' if 'ندارد' in info[5].text else '1'
                    parking = '0' if 'ندارد' in info[6].text else '1'
                    anbari = '0' if 'ندارد' in info[7].text else '1'
                else:
                    asansor = '0' if 'ندارد' in info[3].text else '1'
                    parking = '0' if 'ندارد' in info[4].text else '1'
                    anbari = '0' if 'ندارد' in info[5].text else '1'

                kolle_tabaghat = '0'
                tabaghe = info2[-1].text.replace('همکف', '0')
                if ' از ' in tabaghe:
                    temp = tabaghe.split(' از ')
                    kolle_tabaghat = convert_numbers.persian_to_english(temp[1])
                    tabaghe = convert_numbers.persian_to_english(temp[0])
                else:
                    tabaghe = convert_numbers.persian_to_english(tabaghe)

                sql = "INSERT INTO buyapartment (token, title, location, metraj, sale_sakht, otagh, asansor, anbari, parking, tabaghe, kolle_tabaghat, gheimate_kol, gheimate_har_metr) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                mycursor.execute(sql, (token, title, location, metraj, sale_sakht, otagh, asansor, anbari, parking, tabaghe, kolle_tabaghat, gheimate_kol, gheimate_har_metr))
                mydb.commit()

except WebDriverException as e:
    print(f"WebDriver error occurred: {e}")
finally:
    # Ensure the WebDriver is properly closed
    driver.quit()

    # Close database connection
    mydb.close()
