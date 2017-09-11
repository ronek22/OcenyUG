import requests
from lxml import html
from getpass import getpass

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
        # with open('student.secret') as f:
        #     f = f.readlines()
        #     login,password = f[0].strip().split(':')

        login = raw_input('login: ')
        password = getpass('pass: ')

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


        ####################################
        ####    MAIN PART OF PROGRAM    ####
        ####################################
        lenSem = len(semestry)

        for sem_ID in range(lenSem):
            param = {
                'osobaid':'0',
                'semId':semestry[sem_ID][1],
                'wybierzSemKal':semestry[sem_ID][0]
            }

            # PRZEJSCIE DO WYBRANEGO SEMESTRU
            response = self.session.get(przedmiotyURL,params=param)
            # print "SEMESTRY", response.status_code

            self.sData.append([])

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
                self.sData[sem_ID].append(courseInfo)

            for dane in self.sData[sem_ID]:
                param = {
                    'identyfikatorGUI':dane['gid'],
                    'przedmiotId':dane['pid']
                }

                if dane['pid']==dane['gid'].split('_')[0]:
                    param['osobaId']='0'
                    # ROZWIENIECIE PIERWSZEJ ZAKLADKI
                    response = self.session.get(przedmiotyURL,params=param)

                    # WYCIAGNIECIE ID I GUID PRZEDMIOTU
                    page = html.fromstring(response.content.decode('utf-8'))
                    temp_gid = page.xpath('//a/@id')[0][11:]
                    test = response.text.decode('utf-8')
                    positions = list(self.find_all(test,"var urlParams"))
                    temp_id = self.getPrzedmiotId(positions,test)[0]
                    dane['pid']=temp_id
                    dane['gid']=temp_gid

                    param = {
                        'identyfikatorGUI':dane['gid'],
                        'przedmiotId':dane['pid']
                    }

                    response = self.session.get(wynikiURL,params=param)
                    # print "WYNIK ZAG",dane['name'],dane['gid'],dane['pid'], response.status_code

                    page = html.fromstring(response.content.decode('utf-8'))
                    grade = page.xpath("//td[@style='color: green; vertical-align: middle' or @style='color: red; vertical-align: middle']/text()")[0]
                    grade = "".join(str(grade).split())
                    try:
                        grade = float(grade)
                    except ValueError:
                        pass

                    dane['grade']=grade

                response = self.session.get(wynikiURL,params=param)
                # print "WYNIK",dane['name'],dane['gid'],dane['pid'], response.status_code
                page = html.fromstring(response.content.decode('utf-8'))
                grade = page.xpath("//td[@style='color: green; vertical-align: middle' or @style='color: red; vertical-align: middle']/text()")[0]
                grade = "".join(str(grade).split())
                try:
                    grade = float(grade)
                except ValueError:
                    pass
                dane['grade']=grade
                param = {
                    'osobaid':'0',
                    'semId':semestry[sem_ID][1],
                    'wybierzSemKal':semestry[sem_ID][0]
                }

                # PRZEJSCIE DO WYBRANEGO SEMESTRU
                response = self.session.get(przedmiotyURL,params=param)

        for x in range(lenSem):
            print "%65s" % self.sem2word(semestry[x][0])
            for i in self.sData[x]:
                print "%60s: %3s" % (i['name'],i['grade'])
            print '-'*65
            self.average(self.sData[x])
            print ""







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

        print "%59s: %3.2f" % ("Srednia",(suma/count))

    def sem2word(self,sem):
        next = str(int(sem[:-1])+1)
        if sem[-1] == '1':
            return sem[:-1]+'/'+next+' Zimowy'
        else:
            return sem[:-1]+'/'+next+' Letni'







if __name__ == '__main__':
    kuba = Student()
    kuba.scraper()
