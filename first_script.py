import requests
import xml.etree.ElementTree as ET

URL = "https://www.cbr.ru/scripts/XML_daily.asp"
valutecode = "R01235"
response = requests.get(URL)
data = ET.fromstring(response.content)
for valute in data.findall('Valute'):
        if valute.get('ID') == valutecode:
            name = valute.find('Name').text
            value = valute.find('Value').text
            print(f"Курс {name}: {value} руб.")