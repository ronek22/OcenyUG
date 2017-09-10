import requests
from lxml import html
import sys,unicodedata
import os

BASE_URL = "https://ps.ug.edu.pl:8443/"
loginURL="{}login.web?ajax".format(BASE_URL)
indeksURL="{}wyniki.web".format(BASE_URL)
osURL="{}osCzasu.web?ajax=true".format(BASE_URL)
przedmiotyURL="{}getPrzedmioty.web?ajax=true".format(BASE_URL)
wynikiURL="{}getWyniki.web?ajax=true".format(BASE_URL)
wynikinotAjax = "{}getWyniki.web?".format(BASE_URL)

class Student:

    sData = []

    def __init__(self):
        self.session = requests.session()

    def scraper(self):
        with open('student.secret') as f:
            f = f.readlines()
            login,password = f[0].strip().split(':')

        data = {
            'licznik':'s',
            'login':login,
            'pass':password
        }

        # LOGOWANIE
        response = self.session.post(loginURL,data=data)

        # PRZEJSCIE DO INDEKSU
        response = self.session.get(indeksURL)
        page = html.fromstring(response.content)

        # SZUKANIE KIERUNKOW
        kier = page.xpath('//a/@id')[-1]
        kier = kier[4:]
        att = kier.split('_')

        param = {
            'sciezkaId':att[1],
            'wybierzKier':att[0],
            'osobaId':'0'
        }

        # WYBRANIE KIERUNKU, WYSWIETLENIE LISTY SEMESTROW
        response = self.session.get(osURL,params=param)

        # TWORZENIE LISTY SEMESTROW I ICH ID'kow
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


        param = {
            'osobaid':'0',
            'semId':semestry[0][1],
            'wybierzSemKal':semestry[0][0]
        }

        # PRZEJSCIE DO WYBRANEGO SEMESTRU
        response = self.session.get(przedmiotyURL,params=param)

        #GET PRZEDMIOT ID
        test = response.text.decode('utf-8')
        positions = list(self.find_all(test,"var urlParams"))
        pID = self.getPrzedmiotId(positions,test)

        # ZALADOWANIE DO SLOWNIKA NAZW,ID,GUIID PRZEDMIOTOW
        page = html.fromstring(response.content.decode('utf-8'))
        przedmioty = page.xpath('//a')
        gID = page.xpath('//a/@id')
        gID = [w[11:] for w in gID]
        for x in range(len(przedmioty)):
            course= "".join(przedmioty[x].itertext())
            courseInfo = {
                'name':course,
                'pid':pID[x],
                'gid':gID[x]
            }
            self.sData.append(courseInfo)

        for i in range(len(self.sData)):
            param = {
                'identyfikatorGUI':self.sData[i]['gid'],
                'przedmiotId':self.sData[i]['pid']
            }

            if self.sData[i]['pid']==self.sData[i]['gid'][:-2]:
                param['osobaId']='0'
                response = self.session.get(przedmiotyURL,params=param)
                # print response.status_code
                page = html.fromstring(response.content.decode('utf-8'))
                temp_gid = page.xpath('//a/@id')[0][11:]
                temp_id = int(temp_gid[:-2])+1
                self.sData[i]['pid']=str(temp_id)
                self.sData[i]['gid']=temp_gid

                param = {
                    'identyfikatorGUI':self.sData[i]['gid'],
                    'przedmiotId':self.sData[i]['pid']
                }

                response = self.session.get(wynikiURL,params=param)
                # print response.status_code

                page = html.fromstring(response.content.decode('utf-8'))
                grade = page.xpath("//td[@style='color: green; vertical-align: middle' or @style='color: black; vertical-align: middle']/text()")[0]
                grade = "".join(str(grade).split())
                try:
                    grade = float(grade)
                except ValueError:
                    pass

                self.sData[i]['grade']=grade

            response = self.session.get(wynikiURL,params=param)
            page = html.fromstring(response.content.decode('utf-8'))
            grade = page.xpath("//td[@style='color: green; vertical-align: middle' or @style='color: red; vertical-align: middle']/text()")[0]
            grade = "".join(str(grade).split())
            try:
                grade = float(grade)
            except ValueError:
                pass
            self.sData[i]['grade']=grade
            param = {
                'osobaid':'0',
                'semId':semestry[0][1],
                'wybierzSemKal':semestry[0][0]
            }

            # PRZEJSCIE DO WYBRANEGO SEMESTRU
            response = self.session.get(przedmiotyURL,params=param)

        for i in self.sData:
            print "%45s: %3s" % (i['name'],i['grade'])

        self.average(self.sData)







    def find_all(self, a_str, sub):
        start = 0
        while True:
            start = a_str.find(sub, start)
            if start == -1: return
            yield start
            start += len(sub) # use start += 1 to find overlapping matches

    def getPrzedmiotId(self,pos,stri):
        p = []
        for i in pos:
            a = stri[i+40:i+60]
            b = filter(str.isdigit,str(a))
            p.append(b)
        return p

    def average(self,data):
        count = 0
        suma = 0
        for i in data:
            if isinstance(i['grade'],float):
                count+=1
                suma+=i['grade']

        print "%44s: %3.2f" % ("Srednia: ",(suma/count))







if __name__ == '__main__':
    kuba = Student()
    kuba.scraper()
