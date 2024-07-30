import requests
import mysql.connector
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
import time
import datetime
from unidecode import unidecode

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

mycursor.execute('''
  CREATE TABLE IF NOT EXISTS rentapartment (
      token TEXT,
      title TEXT,
      location TEXT,
      metraj TEXT,
      sale_sakht TEXT,
      otagh INTEGER,
      asansor INTEGER,
      anbari INTEGER,
      parking INTEGER,
      tabaghe INTEGER,
      kolle_tabaghat INTEGER,
      vadie TEXT,
      ejare TEXT,
      vadie_ejare TEXT,
      vadie_calc TEXT
  )
'''
)
mydb.commit()

try:                    
    token = 'gZlaiVyN'
    sql_where = "SELECT token FROM rentapartment WHERE token = %s"
    mycursor.execute(sql_where, (token,))
    token_exist = mycursor.fetchone()

    if not token_exist:
        print('Fetching: https://divar.ir/v/-/' + token)
        driver.get('https://divar.ir/v/-/' + token)
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, 'html.parser')                                

        info = soup.select('tr.kt-group-row__data-row td')
        info2 = soup.select('p.kt-unexpandable-row__value')
        title = soup.select('.kt-page-title__title--responsive-sized')[0].text
        location = soup.select('.kt-page-title__subtitle--responsive-sized')[0].text
        convert_slider = soup.select('.convert-slider__info')

        if convert_slider:
            vadie_ejare = "قابل تبدیل"

            vadie = soup.select('.convert-slider__info .convert-slider__info-right .convert-slider__value')[0].text                                                                                    
            vadie_temp = vadie.replace(' ','').replace('میلیون','').replace('میلیارد','').replace('هزار','')
            temp = unidecode(vadie_temp)
            if 'میلیون' in vadie:
                vadie = str(int(float(temp) * 1000000))
            elif 'میلیارد' in vadie:
                vadie = str(int(float(temp) * 1000000000))
            elif 'هزار' in vadie:
                vadie = str(int(float(temp) * 1000))

            ejare = soup.select('.convert-slider__info .convert-slider__info-right .convert-slider__value')
            if len(ejare) >= 2:
                ejare = ejare[1].text
                ejare_temp = ejare.replace(' ','').replace('میلیون','').replace('میلیارد','').replace('هزار','')
                temp = unidecode(ejare_temp)
                if 'میلیون' in ejare:
                    ejare = str(int(float(temp) * 1000000))
                elif 'میلیارد' in ejare:
                    ejare = str(int(float(temp) * 1000000000))
                elif 'هزار' in ejare:
                    ejare = str(int(float(temp) * 1000))
            else:
                ejare = '0'

        else:
            vadie = unidecode(info2[0].text.replace(' تومان', '').replace('٬', ''))
            ejare = '0' if 'مجانی' in info2[1].text else unidecode(info2[1].text.replace(' تومان', '').replace('٬', ''))
            vadie_ejare = info2[2].text
        

        location = location.split(' پیش در ')[1] if ' پیش در ' in location else location

        metraj = unidecode(info[0].text)
        sale_sakht = unidecode(info[1].text)
        otagh = unidecode(info[2].text.replace('بدون اتاق', '0'))
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
            kolle_tabaghat = unidecode(temp[1])
            tabaghe = unidecode(temp[0])
        else:
            tabaghe = unidecode(tabaghe)

        vadie_calc = int(vadie)
        if int(ejare) > 0:
            vadie_calc = round(int(vadie_calc + ((int(ejare) / 30000) * 1000000)),-5)

        sql = "INSERT INTO rentapartment (token, title, location, metraj, sale_sakht, otagh, asansor, anbari, parking, tabaghe, kolle_tabaghat, vadie, ejare, vadie_ejare , vadie_calc) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        mycursor.execute(sql, (token, title, location, metraj, sale_sakht, otagh, asansor, anbari, parking, tabaghe, kolle_tabaghat, vadie, ejare, vadie_ejare ,str(vadie_calc)))
        mydb.commit()

except WebDriverException as e:
    print(f"WebDriver error occurred: {e}")
finally:
    # Ensure the WebDriver is properly closed
    driver.quit()

    # Close database connection
    mydb.close()
