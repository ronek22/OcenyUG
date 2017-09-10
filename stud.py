import requests
from lxml import html
import sys,unicodedata
import os

loginURL="https://ps.ug.edu.pl:8443/login.web?ajax"
indeksURL="https://ps.ug.edu.pl:8443/wyniki.web"
osURL="https://ps.ug.edu.pl:8443/osCzasu.web?ajax=true"
przedmiotyURL="https://ps.ug.edu.pl:8443/getPrzedmioty.web?ajax=true"

class Student:

    scraped_grades = []

    def __init__(self):
        self.session = requests.session()

    def scraper(self):
        with open('student.secret','r') as f:
            login,password = f.read().split(':')


        data = {
            'licznik':'s',
            'login':login,
            'pass':password
        }

        response = self.session.post(loginURL,data=data)
        # print response.status_code

        # END OF LOGIN
        response = self.session.get(indeksURL)
        page = html.fromstring(response.content)

        kier = page.xpath('//a/@id')[-1]
        kier = kier[4:]
        att = kier.split('_')

        param = {
            'sciezkaId':att[1],
            'wybierzKier':att[0],
            'osobaId':'0'
        }

        response = self.session.get(osURL,params=param)

        page = html.fromstring(response.content)
        sem = page.xpath('//div/@id')
        i = 1
        semestry = []
        for x in sem:
            if i==1:
                a = x[3:7]
                i+=1
            elif i==2:
                b = filter(str.isdigit,x)
                semestry.append([a+'1',b])
                i+=1
            elif i==3:
                b = filter(str.isdigit,x)
                semestry.append([a+'2',b])
                i = 1

        #JAKIS FOR
        param = {
            'osobaid':'0',
            'semId':semestry[0][1],
            'wybierzSemKal':semestry[0][0]
        }

        response = self.session.get(przedmiotyURL,params=param)

        page = html.fromstring(response.content.decode('utf-8'))
        przedmioty = page.xpath('//a')
        for x in przedmioty:
            a= "".join(x.itertext())
            print a






if __name__ == '__main__':
    kuba = Student()
    kuba.scraper()
