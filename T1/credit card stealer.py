from bs4 import BeautifulSoup, Comment
import requests
import csv
from random import randint

def fixformatting(text):
    text = text.replace("&lt;", "")
    text = text.replace("/ul&gt;", "")
    text = text.replace("ul&gt;", "")
    text = text.replace("/br&gt", "")
    text = text.replace("br&gt", "")
    text = text.replace("/p&gt;", "")
    text = text.replace("p&gt;", "")
    text = text.replace("/li&gt;", "")
    text = text.replace("li&gt;", "")
    text = text.replace("&quot;", '\"')
    text = text.replace(";", '\n')
    text= text.replace('\xa0','')
    return text

url = 'https://www.banki.ru/products/creditcards/'
req = requests.get(url)
soup = str(BeautifulSoup(req.content, "html.parser"))
soup = fixformatting(soup)
for i in range(3):
    print(soup.find('offer-product-name'))

