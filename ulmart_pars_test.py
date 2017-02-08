
# -*- coding: utf-8 -*-
from settings import db_user,db_user_pass,db_host,db_name,fromaddr, toaddrs, gmail_login, gmail_pass
import urllib.request as urllib
from mysql.connector import (connection)
from bs4 import BeautifulSoup
import datetime
import smtplib
from email.mime.text import MIMEText


# func to send email via gmail
def send_email(mail_text):
	server = smtplib.SMTP('smtp.gmail.com', 587)
	server.ehlo()
	server.starttls()
	server.login(gmail_login, gmail_pass)
	msg = MIMEText(mail_text)
	msg['Subject'] = "Prices for your goods were chanded"
	msg['From'] = fromaddr
	msg['To'] = toaddrs
	msg['Bcc'] = ""
	server.sendmail(fromaddr, toaddrs,  msg.as_string())
	server.quit()
	return print("Email was sent")

# func to compare prices and create text of email
def Compare_prices(old_row,data,dict):
	count = 0
	mail_text = ""
	if not old_row:
		return 0, mail_text
	for x in range(2,len(data)):
		change = float(old_row[x]) - float(data[x])
		if change != 0:
			if change > 0:
				mail_text =mail_text +("price for {} was decreased by {} \n".format(dict[x],change))
			if change < 0:
				mail_text = mail_text +("price for {} was increased by {} \n".format(dict[x],change*(-1)))
			count = count + 1
	if count>0:
		return 1,mail_text
	else:
		return 0,mail_text


# ========================================================================================================================================
#dict for translating items to names
dict_of_items= {2:"Видеокарта Gigabyte GeForce® GTX 1060, GV-N1060G1 GAMING-6GD, 6ГБ, GDDR5, Retail https://www.ulmart.ru/goods/3949632",
3:'Видеокарта ASUS GeForce® GTX 1060, ROG STRIX-GTX1060-O6G-GAMING, 6ГБ, GDDR5, Retail https://www.ulmart.ru/goods/3953858',
4:"Видеокарта Gigabyte GeForce® GTX 1080, GV-N1080G1 GAMING-8GD, 8ГБ, GDDR5X, Retail  https://www.ulmart.ru/goods/3886464"}


#preparing today's date to insert
date = datetime.datetime.now()
date = date.strftime("%Y-%m-%d")


#parsing and collecting prices
data=[]
urls = ["https://www.ulmart.ru/goods/3949632",'https://www.ulmart.ru/goods/3953858',
		"https://www.ulmart.ru/goods/3886464"]
for url in urls:
	page=urllib.urlopen(url)
	soup = BeautifulSoup(page,"html.parser")
	price=soup.text
	position = price.find('productPrice')+16
	position2 = price.find("'",position)
	data.append(format(float(price[position:position2]),'.2f'))


#sql part
cnx = connection.MySQLConnection(user=db_user, password=db_user_pass,
                                 host=db_host,
                                 database=db_name)
cursor = cnx.cursor()



#get last row, then check seq to inc, set it to one if table is empty
try:
	get_last_raw= "SELECT * FROM Videocards ORDER BY seq DESC LIMIT 1"
	cursor.execute(get_last_raw)
	old_row =[]
	for x in (cursor.fetchone()):
		old_row.append(x)
	next_seq = old_row[1]+1
except TypeError:
	next_seq=1

#preparing list of values to insert
data.insert(0,next_seq)
data.insert(0,date)

#inserting data from list to sql via 
query = "INSERT into Videocards VALUES (%s,%s,%s,%s,%s)"
cursor.execute(query,tuple(data))
print('Info added to sql')

cnx.commit()
cnx.close()


price_changed, mail_text= Compare_prices(old_row,data,dict_of_items)
if price_changed:
	send_email(mail_text)


