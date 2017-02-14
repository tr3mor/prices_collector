# -*- coding: utf-8 -*-
from settings import db_user, db_user_pass, db_host, db_name, fromaddr, toaddrs, gmail_login, gmail_pass
import urllib.request as urllib
from mysql.connector import (connection)
from bs4 import BeautifulSoup
import datetime
import smtplib
from email.mime.text import MIMEText
import re


# func to send email via gmail
def send_email(mail_text):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.login(gmail_login, gmail_pass)
    msg = MIMEText(mail_text, 'html')
    msg['Subject'] = "Prices for your goods were chanded"
    msg['From'] = fromaddr
    msg['To'] = toaddrs
    msg['Bcc'] = ""
    server.sendmail(fromaddr, toaddrs, msg.as_string())
    server.quit()
    print ("Email was sent")
    return 0


# func to compare prices and create text of email
def Compare_prices(old_row, data, dict):
    count = 0
    mail_text = ""
    if not old_row:
        return 0, mail_text
    for x in range(2, len(data)):
        change = float(old_row[x]) - float(data[x])
        if change != 0:
            if change > 0:
                mail_text = mail_text + ("price for {} was decreased by {} <br />".format(dict[x], change))
            if change < 0:
                mail_text = mail_text + ("price for {} was increased by {} <br />".format(dict[x], change * (-1)))
            count = count + 1
    if count > 0:
        return 1, mail_text
    else:
        return 0, mail_text


def get_last_raw(table_name):
    old_row=[]
    try:
        get_last_raw = "SELECT * FROM "+table_name+" ORDER BY seq DESC LIMIT 1"
        cursor.execute(get_last_raw)
        for x in (cursor.fetchone()):
            old_row.append(x)
        next_seq = old_row[1] + 1
    except TypeError:
        next_seq = 1
    return old_row, next_seq


# preparing list of values to insert
def inserting_data(next_seq, date, data, table_name):
    data.insert(0, next_seq)
    data.insert(0, date)
    while len(data) != 5:
        data.append('0')
    # inserting data from list to sql via
    query = "INSERT into "+table_name+" VALUES (%s,%s,%s,%s,%s)"

    cursor.execute(query, tuple(data))
    print('Info added to sql')
    return data

def ulmart_parser(urls):
    data = []
    for url in urls:
        page = urllib.urlopen(url)
        soup = BeautifulSoup(page, "html.parser")
        price = soup.text
        position = price.find('productPrice') + 16
        position2 = price.find("'", position)
        data.append(format(float(price[position:position2]), '.2f'))
    return data


def interes_parser(urls):
    data = []
    for url in urls:
        page = urllib.urlopen(url)
        soup = BeautifulSoup(page, "html.parser")
        price = str(soup.find_all('ins', class_="fl_l"))
        data.append(format(float(re.findall('(\d+)', price)[0]), '.2f'))
    return data

# ========================================================================================================================================
# dict for translating items to names
dict_of_ulmart = {
    2: '<a href="https://www.ulmart.ru/goods/3949632">Видеокарта Gigabyte GeForce® GTX 1060</a>',
    3: '<a href="https://www.ulmart.ru/goods/3953858">Видеокарта ASUS GeForce® GTX 1060</a>',
    4: '<a href="https://www.ulmart.ru/goods/3886464">Видеокарта Gigabyte GeForce® GTX 1080</a>'}
dict_of_interes = {2:'<a href="https://www.1c-interes.ru/catalog/all6968/23177156/">DualShock 4 Cont Magma Red(красный)</a>'}

ulmart_urls = ["https://www.ulmart.ru/goods/3949632", 'https://www.ulmart.ru/goods/3953858',
        "https://www.ulmart.ru/goods/3886464"]
interes_urls = ["https://www.1c-interes.ru/catalog/all6968/23177156/"]


# preparing today's date to insert
date = datetime.datetime.now()
date = date.strftime("%Y-%m-%d")


# sql part
cnx = connection.MySQLConnection(user=db_user, password=db_user_pass,
                                 host=db_host,
                                 database=db_name)
cursor = cnx.cursor()

#parsing
data = []
next_seq = 1


# Ulmart part
# ---------------------------------------------------------------
ulmart_data = ulmart_parser(ulmart_urls)
ulmart_old_data, ulmart_next_seq = get_last_raw('Ulmart')
ulmart_data = inserting_data(ulmart_next_seq, date, ulmart_data, 'Ulmart')
price_changed_ulmart, mail_text_ulmart = Compare_prices(ulmart_old_data, ulmart_data, dict_of_ulmart)
# --------------------------------------------------------------

# 1c_interes part
# -------------------------------------------------------------------
interes_data = interes_parser(interes_urls)
for x in interes_data:
    print(x)
interes_old_data, interes_next_seq = get_last_raw('Interes')
print (interes_next_seq)
interes_data = inserting_data(interes_next_seq,date,interes_data,'Interes')
price_changed_interes, mail_text_interes= Compare_prices(interes_old_data,interes_data,dict_of_interes)

cnx.commit()
cnx.close()

if (price_changed_interes or price_changed_ulmart):
    send_email(mail_text_ulmart+mail_text_interes)


