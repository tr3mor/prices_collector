from bs4 import BeautifulSoup
import urllib.request as urllib
import re
url = "https://www.1c-interes.ru/catalog/all6963/20135814/"
page=urllib.urlopen(url)
soup = BeautifulSoup(page,"html.parser")
price = soup.text
#print(soup)
price=str(soup.find_all('ins',class_="fl_l"))
c=re.findall('(\d+)',price)
print (c[0])
