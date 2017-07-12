#_*_ coding:utf-8 _*_
from six.moves import urllib
from bs4 import BeautifulSoup
from socket import timeout
from json2html import *
import math
import time
import sys
import json
import random
reload(sys)
sys.setdefaultencoding('utf-8')
import xlsxwriter
# review one page 40
class restaurant: #레스토랑의 기본 정보들
    def __init__(self,bs):
        self.name = ""
        self.style =""
        self.pricerange = ""
        self.cuisines = ""
        self.address =""
        self.rating = ""
        self.imgurl = ""
        self.locateurl = ""
        self.set_info_by_url(bs)
    def set_info_by_url(self, bs):# beautifulsoup 객체를 입력받아 정보를 출
        global tmprating
        self.name = bs.find('h1','page-header-title').get_text() # 음식점 이름을 가져옴
        info_content = bs.find_all("div","detail-content")
        self.style = info_content[0].get_text() # 식당스타일
        try:
            self.pricerange = info_content[4].get_text().encode("utf-8") # 가격범위
        except:
            print "가격범위오류"
        self.cuisines = info_content[3].get_text() #요리법
        self.address = bs.find( itemprop='streetAddress').get_text()
        try:
            self.rating = bs.find("div","all-stars filled").get('title')
        except:
            self.rating = tmprating
        try:
            self.imgurl = bs.find(itemprop ='image').get('src')
        except:
            self.imgurl ="NONE"
        try:
            self.locateurl = bs.find("img","sidebar-map-img").get('src')
        except:
            try:
                time.sleep(1)
                self.locateurl = bs.find("img", "sidebar-map-img").get('src')
            except:
                self.locateurl ="Accecss time over"
        #print self.imgurl
        #print self.locateurl
    def printinfo(self):
        print self.name
        print self.style
        print self.pricerange
        print self.cuisines
        print self.address
class get_review_keword:
    def __init__(self,filename):
        self.keyword = [] # 등급별 키워드 2차원배열
        self.gradecnt = 0 #등급이 몇분류 까지 되어있는지
        with open(filename, "r") as f:
            line = f.read().decode("utf-8-sig").encode("utf-8")
            content = line.split('@')
            grade_list = []
            for i in range(0, len(content)):
                if not content[i] == '':
                    grade_list.append(content[i].strip())#공백제거
            self.gradecnt = len(grade_list) #몇등급 분류되어있는지 가져온다

            for keyword in grade_list:
                key = keyword.split(":")[1]
                #print key
                self.keyword.append(list(key.split(','))) # 2차원 배열로 정리
            #print self.keyword , len(self.keyword), (self.gradecnt)
class get_food_character:
    def __init__(self, filename):
        self.keyword = []  # 푸드특성 키워드 2차원배열
        self.character = [] # 푸드특성 : fresh 같은거 1차원배열
        self.charcnt = 0  # 특성이 몇분류 까지 되어있는지
        with open(filename, "r") as f:
            line = f.read().decode("utf-8-sig").encode("utf-8")
            content = line.split('@')
            char_list = []
            for i in range(0, len(content)):
                if not content[i] == '':
                    char_list.append(content[i].strip())  # 공백제거
            self.charcnt = len(char_list)  # 몇등급 분류되어있는지 가져온다
            #print char_list
            for charword in char_list:
                 (char,key) = charword.split(":")
                 self.character.append(char.split('[')[1].split(']')[0])
                 #print key
                 self.keyword.append(list(key.split(',')))  # 2차원 배열로 정리
            #print self.character
            #print self.keyword , len(self.keyword)
def get_menulist(bs):
    menu_content = bs.find_all("div", "rest-menu-item-title")
    menu_list = []
    for i in menu_content:
        try:
            menu_list.append(i.get_text().encode('utf-8'))
        except:
            print "메뉴오류"
    return menu_list
def get_reviewlist(bs, url):
    review_list = []
    page = "?page="
    review_cnt = bs.find("div", "reviews-count color-light")
    try:
        review_cnt = review_cnt.get_text().split(' ')[0]
    except:
        print "리뷰없음"
        return review_list.append("none")

    pnum = (float)(review_cnt)/40 # 한페이지에 40개씩 저장됨, 예를 들면 52개의 리뷰면 2페이지까지 있다는 소리
    pnum = int(math.ceil(pnum))  # pnum을 마지막 페이지까지 설정
    #print pnum
    for pidx in range(1,pnum+1):
        html = url + page + str(pidx)
        IsOpen = False
        roofescape = 0
        while not IsOpen:
            roofescape += 1
            if roofescape == 10:
                break;  # 없는거임 url
            try:
                f = urllib.request.urlopen(html)
                IsOpen = True
            except:
                urllib.request.urlcleanup()
                print "재시도중1"
                try:
                    f = urllib.request.urlopen(html)
                    IsOpen = True
                except:
                    urllib.request.urlcleanup()
                    print "리셋후재시도중1"
        resultXML = f.read()
        reviewbs = BeautifulSoup(resultXML, "lxml")
        review_content = reviewbs.find_all("div", "review-content")
        for i in review_content:
            txt = ""
            for j in i.find_all('p'):
                try:
                    txt = txt + j.get_text().encode("utf-8")
                except:
                    print "리뷰오류"
            review_list.append(txt)
    return review_list

class collection: # 원하시는 리뷰 목록 등을 수집하는 필터링된 데이터만 들어오는 클래스
    def __init__(self):
        self.collected_address = "" #음식점주소
        self.collected_cnt = 0 # 수집된 리뷰의 정보의수
        self.collected_review = [] #수집된 리뷰 리스트 키워드가 있으면 걸림
        self.collected_food = []  # 해당키워드에 걸린 푸드리스트, 일차
        self.collected_score = [] # 음식의 grade별로 점수(언급횟수) 2차원배열
        self.collected_character = [] # 해당키워드에 걸린 푸드의 특징2차원배열
        self.foodidx_list=[] # 실행속도를 높이기위해 food가 있는 review 리스트의 idx
        self.keywordcnt = 0
    def set_reveiwAndscore(self,review): # 키워드에 걸린 리뷰를 저장  + cnt갯수 증가
        self.collected_cnt = self.collected_cnt + 1
        self.collected_review.append(review)
    def filter_review(self, reviewlist):#여기서 해야할껀 키워드별 하나라도 걸리면 이클래스의 리뷰리스트에저장하는거
        global keword_class
        self.keywordcnt = keword_class.gradecnt
        try:
            for review in reviewlist:  # 전체 리뷰를 돌면서
                reviewtxt = review.lower()  # 모든 문자를 소문자로 변환
                for gradeidx in range(0, keword_class.gradecnt): # 등급을 매기는 키워드 idx 끝까지돌면서
                    for keyword in keword_class.keyword[gradeidx]:# 반환값은 해당 idx의 키워드 리스트
                        if not reviewtxt.find(keyword) == -1:  # 하나라도 찾았다
                            self.set_reveiwAndscore(reviewtxt)
                            break;
        except:
            pass
    def extract_food(self, menulist): #댓글에서 언급된 메뉴이름을 저장한다. 완벽하게 일치해야 한다는 문제점이있음
        global keword_class
        self.collected_review = list(set(self.collected_review)) # 중복제거
        for food in menulist: #메뉴리스트를 하나씩 돌면서
            foodscore = [0 for i in range(self.keywordcnt)] #푸드마다 스코어 리스트생성
            idx = 0
            for review in self.collected_review: #리뷰리스트를 돈다
                reviewtxt = review.lower()
                foodtxt = food.lower()
                if not reviewtxt.find(foodtxt) == -1: #리뷰속에서 음식을 찾으면
                    IsExist = False
                    try:
                        foodidx =self.collected_food.index(food)#이미 수집음식목록에 있나본다
                        foodscore = self.collected_score[foodidx]
                        self.foodidx_list.append(idx)
                        IsExist = True
                    except: #없을경우
                        #print "처음"
                        IsExist = False
                        self.collected_food.append(food)  # 음식을 추가하고
                        self.foodidx_list.append(idx)
                    #자이제 등급을 매기자, 똑같은 음식이 두번올수도 있자나
                    for gradeidx in range(0, keword_class.gradecnt):  # 등급을 매기는 키워드 idx 끝까지돌면서
                        for keyword in keword_class.keyword[gradeidx]:  # 반환값은 해당 idx의 키워드 리스트
                            if not reviewtxt.count(keyword) == 0: #하나라도 있다, 추가시켜주기
                                foodscore[gradeidx] = foodscore[gradeidx] + reviewtxt.count(keyword) #스코어 값늘려주기
                    if not IsExist:#없으면 추가
                        self.collected_score.append(foodscore)
                idx = idx + 1
    def matching_food_character(self,defaultchar):
        global char_class

        for idx in range (0,len(self.collected_food)): # 음식리스트를 돌면서
            chartxt = defaultchar  # 음식특징에 기본값을 부여
            foodtxt = self.collected_food[idx].lower()
            for charidx in range(0,char_class.charcnt): # 인덱스돌면
                for keyword in char_class.keyword[charidx]: #키워드를봄
                    if not foodtxt.find(keyword) == -1:  # 있다
                        chartxt = chartxt + ", "+char_class.character[charidx] #성질부여
            self.collected_character.append(chartxt)



def get_infotest(urllist, workbook2):
    global char_class
    #url = "https://www.opentable.co.uk/beautique" #적당
    #url = "https://www.opentable.co.uk/scarlatto" #리뷰많음
    #url = "https://www.opentable.co.uk/r/carousel-royal-plaza-on-scotts" #리뷰없음
    #url = "https://www.opentable.com/8-mount-street"
    idx = 1
    for url in urllist:
        print idx , " 개 처리중.."
        idx += 1
        page = "?page="
        p_num = 1
        html = url + page + str(p_num)
        print html
        IsOpen = False
        roofescape = 0
        while not IsOpen:
            roofescape += 1
            if roofescape == 10:
                break;  # 없는거임 url

            try:
                f = urllib.request.urlopen(html)
                IsOpen = True
            except:
                urllib.request.urlcleanup()
                print "재시도중"
                try:
                    f = urllib.request.urlopen(html)
                    IsOpen = True
                except:
                    print "리셋후재시도중"
                    pass
        if not roofescape == 10:
            resultXML = f.read()
            bs = BeautifulSoup(resultXML,"lxml")
            menu_list = get_menulist(bs) # 메뉴리스트를 가져옴
            restaurant_info = restaurant(bs) #레스토랑의 정보들을 가져옴
            #리뷰의 전체목록을 가져옴
            review_list = get_reviewlist(bs, url)  # 리뷰 리스트들을 가져옴
            collectclass = collection() # 수집할 클래스 에 댓글목록을 넣어줌
            collectclass.collected_address = restaurant_info.address # 가게의 주소입력
            collectclass.filter_review(review_list) # keyword에 단어가 있는것만 추려냄
            collectclass.extract_food(menu_list)
            collectclass.matching_food_character(restaurant_info.cuisines)
            #print collectclass.collected_food
            #for i in collectclass.foodidx_list:
            #    print collectclass.collected_review[i]
            #print collectclass.collected_score
            #print collectclass.collected_character
            #print collectclass.collected_review
            make_excel(collectclass,restaurant_info,1,workbook2)
#def get_info(_url):
#    global char_class
#    # 원래url = _url.strip()
#    #url = "https://www.opentable.co.uk/beautique" #적당
#    #url = "https://www.opentable.co.uk/scarlatto" #리뷰많음
#    #url = "https://www.opentable.co.uk/r/carousel-royal-plaza-on-scotts" #리뷰없음
#    url = "https://www.opentable.com/8-mount-street"
#    page = "?page="
#    p_num = 1
#    html = url + page + str(p_num)
#    try:
#        f = urllib.request.urlopen(html, timeout=10)
#    except timeout:
#        urllib.request.urlcleanup()
#        f = urllib.request.urlopen(html, timeout=5)
#    resultXML = f.read()
#    bs = BeautifulSoup(resultXML,"lxml")
#    menu_list = get_menulist(bs) # 메뉴리스트를 가져옴
#    restaurant_info = restaurant(bs) #레스토랑의 정보들을 가져옴
#    #리뷰의 전체목록을 가져옴
#    review_list = get_reviewlist(bs, url)  # 리뷰 리스트들을 가져옴
#    collectclass = collection() # 수집할 클래스 에 댓글목록을 넣어줌
#    collectclass.collected_address = restaurant_info.address # 가게의 주소입력
#    collectclass.filter_review(review_list) # keyword에 단어가 있는것만 추려냄
#    collectclass.extract_food(menu_list)
#    collectclass.matching_food_character(restaurant_info.cuisines)
#    print collectclass.collected_food
#    for i in collectclass.foodidx_list:
#        print collectclass.collected_review[i]
#    print collectclass.collected_score
#    print collectclass.collected_character
#    # print collectclass.collected_review
#    make_excel(collectclass,restaurant_info)
def make_excel(collectclass, restaurantinfoclass ,parsingrange =1,workbook2=''):
    global keword_class
    for i in range(0,parsingrange):
        #열 넓이 조정
        try:
            a = ['[', ']', ':', '*', '?', '/']
            b = ' \ '
            if workbook2.get_worksheet_by_name(restaurantinfoclass.name[:10]) == None:
                worksheet = workbook2.add_worksheet(restaurantinfoclass.name[:10])
            else:
                print "중복된 이름시트존재"
                a.append(b.strip())
                name = str(restaurantinfoclass.name[:8])
                name = "(" + str(random.randint(1, 100)) + ")_" + name
                for i in a:
                    name = name.replace(i, '')
                worksheet = workbook2.add_worksheet(name)
        except:
            print "워크시트이름 오류"
            print str(restaurantinfoclass.name[:10])
            a.append(b.strip())
            name = str(restaurantinfoclass.name[:10])
            for i in a:
                name = name.replace(i,'')
            try:
                worksheet = workbook2.add_worksheet(name)
            except:
                print "워크시트 중복된거"
                name = str(restaurantinfoclass.name[:8])
                name = "((" + str(random.randint(1, 100)) + "))_" + name
                for i in a:
                    name = name.replace(i, '')
                worksheet = workbook2.add_worksheet(name)

        worksheet.set_column('A:A', 6)#레이팅
        worksheet.set_column('B:B', 25)#주소
        worksheet.set_column('C:C',20)#업체이름
        col_list = ['D','E','F','G','H','I','J','K','L','M','N','O']
        for j in range(0,keword_class.gradecnt):#레이팅적는곧
            worksheet.set_column(col_list[j]+ ":"+col_list[j], 6)
        sangidx = keword_class.gradecnt
        worksheet.set_column(col_list[sangidx]+ ":"+col_list[sangidx], 15)  #  상품특징
        blankidx = sangidx+1
        worksheet.set_column(col_list[blankidx] + ":" + col_list[blankidx], 2)  # 빈칸
        reidx = blankidx+1
        worksheet.set_column(col_list[reidx] + ":" + col_list[reidx],100)  # 리뷰
        #첫줄
        format = workbook2.add_format()
        format.set_font_size(8)
        format.set_bold()
        format.set_align('center')
        format.set_bg_color('yellow')
        format.set_border(True)
        #한글은 앞에 u자붙여라
        worksheet.write('A1', "Rating" , format)
        worksheet.write('B1', u"업체명(위) / 주소(아래)", format)
        worksheet.write('C1', u"음식명", format)
        for k in range(0,keword_class.gradecnt):#레이팅적는곧
            worksheet.write(col_list[k]+ "1", "["+str(k+1)+"]", format)
        worksheet.write(col_list[sangidx] + "1", u"상품특징" , format)
        worksheet.write(col_list[blankidx] + "1", "", format)
        worksheet.write(col_list[reidx] + "1", "filltered review", format)
        # Write some numbers, with row/column notation.
        #첫뻔째가 0행 0열임
        format = workbook2.add_format()
        format.set_font_size(8)
        format.set_align('center')
        spformat = workbook2.add_format()
        spformat.set_font_size(8)
        spformat.set_align('center')
        spformat.set_bg_color('red')
        IsFirst = True
        row_start = 1 #시작할 행넘버
        if IsFirst:  # 처음이면
            worksheet.write(row_start, 0, restaurantinfoclass.rating, format)
            worksheet.write(row_start, 1, restaurantinfoclass.name, format)
            worksheet.write(row_start + 1, 1, restaurantinfoclass.address, format)
            worksheet.write(row_start + 2, 1, u"식당사진(위) / 지도사진(아래)", format)
            worksheet.write(row_start + 3, 1, restaurantinfoclass.imgurl, format)
            worksheet.write(row_start + 4, 1, restaurantinfoclass.locateurl, format)
            IsFirst = False
        for idx in range( 0,len(collectclass.collected_food)): # 수집된 음식 개수만큼돈다
            worksheet.write(row_start, 2,collectclass.collected_food[idx],format)
            for q in range(0, keword_class.gradecnt):  # 레이팅적는곧
                worksheet.write(row_start,3+q, collectclass.collected_score[idx][q],format)
            worksheet.write(row_start, 2, collectclass.collected_food[idx],format)
            worksheet.write(row_start, 3+ keword_class.gradecnt, collectclass.collected_character[idx],format)
            row_start +=1
        row_start = 1  # 시작할 행넘버
        #blankidx reidx
        blankidx = blankidx+3
        reidx = reidx +3 # 레이팅, 주소, 음식명이 3개니까

        for idx in range(0, len(collectclass.collected_review)): #리뷰 를 출력할것
            try:
                collectclass.foodidx_list.index(idx) #찾았는데 있다 음식키워드가 있던글
                worksheet.write(row_start, blankidx, idx+1,spformat)
                worksheet.write(row_start, reidx, (collectclass.collected_review[idx].decode('cp949')),format)
            except:#없다
                worksheet.write(row_start, blankidx, idx+1,format)
                try:
                    worksheet.write(row_start, reidx, (collectclass.collected_review[idx].decode('cp949')),format)
                except:
                    #print (collectclass.collected_review[idx])
                    print("인코딩변환 시도")
                    try:
                        worksheet.write(row_start, reidx, (collectclass.collected_review[idx].decode('utf-8')), format)
                    except:
                        print("인코딩오류")
                        worksheet.write(row_start, reidx, ("encoding error"), format)
            row_start+=1


        # Insert an image.
        #worksheet.insert_image('B5', 'logo.png')

# 전체페이지에서 레스토랑을 검색하고 url목록을 다가져온다
# for 그 개수만큼
# collection 클래스에 = getinfo () 를 해서 저장
# collection 클래스에 있는 정보는 수집된 댓글수, 수집된 리뷰, 리뷰에 언급된 푸드리스트,  그 음식별 스코어, 그 음식의 특징 이렇게 가지고있다
# 그럼그걸 [도시이름].xls 파일에 worksheet를 추가하여 저장만 하기만 하면됨
keword_class = get_review_keword("grade.txt") #키워드 등급정보가 있는 파일이름을 적으면됨 클래스 객체 반환
char_class = get_food_character('character.txt')#푸드 특성별 정보가 있는 파일이름 클래스 객체 반환
#workbook = xlsxwriter.Workbook("test2.xlsx")
workbook = ""
xlsext =".xlsx"
def Command():
    global metroallid
    # metro id 만 알고 저기에
    # from0 부터 넣음다음
    global tmprating
    _url = "https://www.opentable.co.uk/s/node/api?covers=2&currentview=list&size=100&sort=Popularity&PageType=2"
    fromtxt = "&from="
    fromidx = 0
    metrotxt = "&metroid="
    metroid = metroallid  # 하와이
    url = _url + metrotxt + str(metroid) + fromtxt + str(fromidx)
    # data-clear-metro-history 에 메트로시티 번호가 있는거 같다 이건 전체번호고
    rating = raw_input("몇이상 rating?:")
    ratingmax = raw_input("몇이하 rating?:")
    rating = float(rating)
    ratingmax = float(ratingmax)
    tmprating = rating
    IsOpen = False
    roofescape = 0
    while not IsOpen:
        roofescape += 1
        if roofescape == 10:
            break;  # 없는거임 url
        try:
            f = urllib.request.urlopen(url)
            IsOpen = True
        except:
            urllib.request.urlcleanup()
            print "재시도중3"
            try:
                f = urllib.request.urlopen(url)
                IsOpen = True
            except:
                print "리셋후재시도중3"
                pass
    data = f.read()
    j = json.loads(data)
    total = j['Results']['TotalAvailable']
    name = j['Results']['Restaurants']
    urilist = []
    ratinglist = []
    basic_url = "https://www.opentable.com"
    forrange = int(math.ceil(float(total) / 100))
    filetitle = (j['Display']['SearchBigHeading']).split(' ')[1]
    print filetitle, "총 ", total, "개 가 있습니다."
    for roof in range(1, forrange + 1):
        print url
        for i in name:
            try:
                if i['Reviews']['Rating'] >= rating and i['Reviews']['Rating'] <= ratingmax:
                    ratinglist.append(i['Reviews']['Rating'])
                    try:
                        urilist.append(basic_url + (i['ProfileUri']).encode('utf-8'))
                    except:
                        pass
            except:
                pass
        fromidx = (100 * roof)
        url = _url + metrotxt + str(metroid) + fromtxt + str(fromidx)
        IsOpen = False
        roofescape = 0
        while not IsOpen:
            roofescape += 1
            if roofescape == 10:
                break;  # 없는거임 url

            try:
                f = urllib.request.urlopen(url)
                IsOpen = True
            except:
                urllib.request.urlcleanup()
                print  "재시도중2"
                try:
                    f = urllib.request.urlopen(url)
                    IsOpen = True
                except:
                    print "리셋후재시도중2"
                    pass
        data = f.read()
        j = json.loads(data)
        total = j['Results']['TotalAvailable']
        name = j['Results']['Restaurants']
    print "조건에 맞는 ", len(ratinglist), " 개 검색완료"
    print urilist
    print len(urilist)
    return 1
    extractrange = raw_input("뽑을 시작인덱스 (시작 1):")
    extractrangemax = raw_input("뽑을 마지막인덱스(총 100개면 마지막 100):")
    sheetnum = raw_input("한파일에 몇시트씩:")
    # print len(urilist[int(extractrange)-1:int(extractrangemax)])
    # 27개를 5시트씩 뽑는다하면
    callnum = float(int(extractrangemax) - int(extractrange) + 1) / int(sheetnum)
    callnum = int(math.ceil(callnum))
    print callnum
    startidx = (int(extractrange) - 1)
    endidx = startidx + int(sheetnum)
    #workbook2 = xlsxwriter.Workbook(str(filetitle)  + ".xlsx")
    with xlsxwriter.Workbook(str(filetitle)  + ".xlsx") as workbook2:
        get_infotest(urilist[startidx:endidx], workbook2)
    #workbook2.close()
    #for idx in range(0, callnum):
    #    workbook2 = xlsxwriter.Workbook(str(filetitle)+str(idx)+".xlsx")
    #    startidx = (int(extractrange) - 1) + int(sheetnum) * idx
    #    endidx = startidx + int(sheetnum)
    #    if endidx >= int(extractrangemax):
    #        endidx = int(extractrangemax)
    #    print len(urilist[startidx:endidx]), startidx, endidx
    #    get_infotest(urilist[startidx:endidx],workbook2)
    #    workbook2.close()
# url 입력하세요
# rating 범위 몇이상, 몇이하
# 개수는 몇갭니다 알려주고
# 몇부터 몇까지 추출하시겠어요
# 몇개단위로 저장할까요
tmprating=0
# data-clear-metro-history 에 메트로시티 번호가 있는거 같다 이건 전체번호고
#하와이 34
#싱가폴 285
#옥스퍼드 3101
#캠브릿지 3122
#멜버른 279
#시카고 3
#샌프란 4
metroallid = 4
def __main__():
    #Command()
    #"""
    #
    # 샌프란 1312개개
    #
    a = ['https://www.opentable.com/r/finn-town-tavern-san-francisco', 'https://www.opentable.com/flour-and-water', 'https://www.opentable.com/r/aina-san-francisco', 'https://www.opentable.com/gary-danko', 'https://www.opentable.com/r/hinata-sushi-san-francisco', 'https://www.opentable.com/otd-aka-out-the-door-bush-st', 'https://www.opentable.com/meadowood-the-restaurant', 'https://www.opentable.com/wood-tavern', 'https://www.opentable.com/kokkari-estiatorio', 'https://www.opentable.com/evvia', 'https://www.opentable.com/als-place', 'https://www.opentable.com/asiasf', 'https://www.opentable.com/acquerello', 'https://www.opentable.com/zuni-cafe', 'https://www.opentable.com/r/boulevard-san-francisco', 'https://www.opentable.com/flea-street-cafe', 'https://www.opentable.com/farmstead-at-long-meadow-ranch', 'https://www.opentable.com/terrapin-creek-cafe-and-restaurant', 'https://www.opentable.com/r/fondue-cowboy-san-francisco', 'https://www.opentable.com/house-of-prime-rib', 'https://www.opentable.com/picco-restaurant', 'https://www.opentable.com/cafe-la-haye', 'https://www.opentable.com/zola-palo-alto', 'https://www.opentable.com/omakase', 'https://www.opentable.com/lardoise', 'https://www.opentable.com/r/pizzeria-delfina-burlingame', 'https://www.opentable.com/la-ciccia', 'https://www.opentable.com/va-de-vi-bistro-and-wine-bar', 'https://www.opentable.com/bouchon-yountville', 'https://www.opentable.com/valette', 'https://www.opentable.com/the-french-laundry', 'https://www.opentable.com/r/home-soquel', 'https://www.opentable.com/frances', 'https://www.opentable.com/st-francis-winery-and-vineyards', 'https://www.opentable.com/el-techo', 'https://www.opentable.com/r/delfina-restaurant-san-francisco', 'https://www.opentable.com/flemings-steakhouse-palo-alto', 'https://www.opentable.com/leos-oyster-bar', 'https://www.opentable.com/waterbar', 'https://www.opentable.com/frascati', 'https://www.opentable.com/seven-hills', 'https://www.opentable.com/the-rotunda-at-neiman-marcus', 'https://www.opentable.com/jackson-fillmore-trattoria', 'https://www.opentable.com/trestle', 'https://www.opentable.com/rich-table', 'https://www.opentable.com/naschmarkt-restaurant', 'https://www.opentable.com/bar-crudo-divisadero-st', 'https://www.opentable.com/akikos-restaurant-and-sushi-bar', 'https://www.opentable.com/sams-chowder-house', 'https://www.opentable.com/saison', 'https://www.opentable.com/foreign-cinema', 'https://www.opentable.com/original-joes-westlake', 'https://www.opentable.com/tonga-room-and-hurricane-bar-fairmont-san-francisco', 'https://www.opentable.com/mamacita', 'https://www.opentable.com/coles-chop-house', 'https://www.opentable.com/orexi', 'https://www.opentable.com/balboa-cafe-sf', 'https://www.opentable.com/r/locanda-osteria-and-bar-san-francisco', 'https://www.opentable.com/bottega-napa-valley', 'https://www.opentable.com/nico-san-francisco', 'https://www.opentable.com/the-progress', 'https://www.opentable.com/town-san-carlos', 'https://www.opentable.com/bird-dog', 'https://www.opentable.com/buckeye-roadhouse', 'https://www.opentable.com/r/trading-post-restaurant-cloverdale', 'https://www.opentable.com/cotogna', 'https://www.opentable.com/the-richmond', 'https://www.opentable.com/zero-zero', 'https://www.opentable.com/r/sasaki-san-francisco', 'https://www.opentable.com/r/tartine-manufactory-san-francisco', 'https://www.opentable.com/z-and-y-restaurant', 'https://www.opentable.com/manresa-los-gatos', 'https://www.opentable.com/wayfare-tavern', 'https://www.opentable.com/press', 'https://www.opentable.com/benu', 'https://www.opentable.com/the-restaurant-at-wente-vineyards', 'https://www.opentable.com/ju-ni', 'https://www.opentable.com/ad-hoc', 'https://www.opentable.com/stones-throw', 'https://www.opentable.com/630-park-steakhouse-graton-resort-and-casino', 'https://www.opentable.com/john-bentleys-redwood-city', 'https://www.opentable.com/ruths-chris-steak-house-walnut-creek', 'https://www.opentable.com/wako-japanese-restaurant', 'https://www.opentable.com/forbes-mill-steakhouse-los-gatos', 'https://www.opentable.com/octavia', 'https://www.opentable.com/all-spice-san-mateo', 'https://www.opentable.com/redd', 'https://www.opentable.com/lolinda', 'https://www.opentable.com/mustards-grill', 'https://www.opentable.com/enoteca-molinari', 'https://www.opentable.com/alexanders-steakhouse-sf', 'https://www.opentable.com/auberge-du-soleil', 'https://www.opentable.com/trattoria-corso', 'https://www.opentable.com/the-bull-valley-roadhouse', 'https://www.opentable.com/absinthe-brasserie-and-bar', 'https://www.opentable.com/perbacco-san-francisco', 'https://www.opentable.com/bix', 'https://www.opentable.com/the-village-pub', 'https://www.opentable.com/sir-and-star-at-the-olema', 'https://www.opentable.com/r/true-food-kitchen-walnut-creek', 'https://www.opentable.com/r/farmhouse-kitchen-thai-cuisine-san-francisco', 'https://www.opentable.com/paradise-beach-grille', 'https://www.opentable.com/park-tavern-san-francisco', 'https://www.opentable.com/gyu-kaku-cupertino', 'https://www.opentable.com/marche-aux-fleurs', 'https://www.opentable.com/cafe-at-the-opera', 'https://www.opentable.com/greens-restaurant-san-francisco', 'https://www.opentable.com/fog-harbor-fish-house', 'https://www.opentable.com/mourad', 'https://www.opentable.com/el-paseo-mill-valley', 'https://www.opentable.com/solbar-solage', 'https://www.opentable.com/perrys-on-magnolia', 'https://www.opentable.com/kincaids-bayhouse-burlingame', 'https://www.opentable.com/r/mister-jius-san-francisco', 'https://www.opentable.com/hakkasan-san-francisco', 'https://www.opentable.com/r/waterdog-tavern-belmont', 'https://www.opentable.com/koh-samui-and-the-monkey', 'https://www.opentable.com/r/true-food-kitchen-palo-alto', 'https://www.opentable.com/flemings-steakhouse-walnut-creek', 'https://www.opentable.com/spruce', 'https://www.opentable.com/r/il-fornaio-santa-clara', 'https://www.opentable.com/harvest-moon-cafe', 'https://www.opentable.com/nm-cafe-at-neiman-marcus-walnut-creek', 'https://www.opentable.com/bungalow-44', 'https://www.opentable.com/riva-cucina', 'https://www.opentable.com/boca-tavern', 'https://www.opentable.com/benihana-burlingame', 'https://www.opentable.com/r/royal-exchange-san-francisco', 'https://www.opentable.com/the-hideout-kitchen-and-cafe', 'https://www.opentable.com/outerlands', 'https://www.opentable.com/alexanders-steakhouse-cupertino', 'https://www.opentable.com/panama-hotel-and-restaurant', 'https://www.opentable.com/terra-restaurant-st-helena', 'https://www.opentable.com/dry-creek-kitchen', 'https://www.opentable.com/hong-kong-lounge-ii', 'https://www.opentable.com/benihana-concord', 'https://www.opentable.com/madera-rosewood-hotel-sand-hill', 'https://www.opentable.com/gather', 'https://www.opentable.com/belotti-ristorante-e-bottega', 'https://www.opentable.com/le-ptit-laurent', 'https://www.opentable.com/black-sheep-brasserie', 'https://www.opentable.com/a-cote', 'https://www.opentable.com/harris', 'https://www.opentable.com/mizu-sushi-bar-and-grill', 'https://www.opentable.com/pabu-san-francisco', 'https://www.opentable.com/reposado-restaurant', 'https://www.opentable.com/monsieur-benjamin', 'https://www.opentable.com/gyu-kaku-san-mateo', 'https://www.opentable.com/capos-chicago-pizza-and-fine-italian-dinners', 'https://www.opentable.com/presidio-social-club', 'https://www.opentable.com/amber-india-san-francisco', 'https://www.opentable.com/sams-social-club', 'https://www.opentable.com/redd-wood', 'https://www.opentable.com/shakewell', 'https://www.opentable.com/millennium-oakland', 'https://www.opentable.com/rasa-burlingame', 'https://www.opentable.com/sundance-the-steakhouse', 'https://www.opentable.com/the-lexington-house', 'https://www.opentable.com/r/j-vineyards-and-winery-healdsburg', 'https://www.opentable.com/marlowe', 'https://www.opentable.com/wine-spectator-greystone-restaurant-at-the-culinary-institute-of-america-st-helena', 'https://www.opentable.com/laili', 'https://www.opentable.com/piatti-danville', 'https://www.opentable.com/terzo', 'https://www.opentable.com/postino', 'https://www.opentable.com/ladera-grill-morgan-hill', 'https://www.opentable.com/mason-pacific', 'https://www.opentable.com/benihana-cupertino', 'https://www.opentable.com/coqueta', 'https://www.opentable.com/black-angus-steakhouse-blossom-hill', 'https://www.opentable.com/central-kitchen', 'https://www.opentable.com/rangoon-ruby-burmese-cuisine-palo-alto', 'https://www.opentable.com/farmshop-marin', 'https://www.opentable.com/padrecito', 'https://www.opentable.com/r/mescolanza-san-francisco', 'https://www.opentable.com/bistro-central-parc-sf', 'https://www.opentable.com/contigo', 'https://www.opentable.com/maggianos-san-jose', 'https://www.opentable.com/barbacco', 'https://www.opentable.com/forbes-island', 'https://www.opentable.com/odeum', 'https://www.opentable.com/rivoli-restaurant', 'https://www.opentable.com/yoshis-oakland', 'https://www.opentable.com/r/pintxopote-los-gatos', 'https://www.opentable.com/r/kenzo-napa', 'https://www.opentable.com/bellanico-restaurant-and-wine-bar', 'https://www.opentable.com/gracias-madre-sf', 'https://www.opentable.com/rustic-franciss-favorites', 'https://www.opentable.com/garibaldis-on-presidio', 'https://www.opentable.com/insalatas', 'https://www.opentable.com/revel-kitchen-and-bar', 'https://www.opentable.com/bazille-nordstrom-valley-fair', 'https://www.opentable.com/cindys-backstreet-kitchen', 'https://www.opentable.com/yank-sing-stevenson-street', 'https://www.opentable.com/r/uncle-yus-at-the-vineyard-livermore', 'https://www.opentable.com/bumble', 'https://www.opentable.com/poggio', 'https://www.opentable.com/r/palmento-a-dopo-oakland', 'https://www.opentable.com/graces-table', 'https://www.opentable.com/chianti-cucina-novato', 'https://www.opentable.com/ruths-chris-steak-house-san-francisco', 'https://www.opentable.com/mortons-the-steakhouse-san-jose', 'https://www.opentable.com/chaya-brasserie', 'https://www.opentable.com/bridges-restaurant', 'https://www.opentable.com/navio', 'https://www.opentable.com/adega-san-jose', 'https://www.opentable.com/la-posta', 'https://www.opentable.com/montecatini-restaurant-walnut-creek', 'https://www.opentable.com/black-angus-steakhouse-dublin', 'https://www.opentable.com/sweet-ts-restaurant-and-bar', 'https://www.opentable.com/pampas-palo-alto', 'https://www.opentable.com/original-joes-san-francisco', 'https://www.opentable.com/oliveto-cafe-and-restaurant', 'https://www.opentable.com/teleferic-barcelona', 'https://www.opentable.com/cascal', 'https://www.opentable.com/sea-thai-bistro-santa-rosa', 'https://www.opentable.com/r/august-1-five-san-francisco', 'https://www.opentable.com/the-sea-by-alexanders-steakhouse-palo-alto', 'https://www.opentable.com/the-dead-fish', 'https://www.opentable.com/milagros', 'https://www.opentable.com/il-fornaio-walnut-creek', 'https://www.opentable.com/cucina-sa', 'https://www.opentable.com/martins-west-pub', 'https://www.opentable.com/fogo-de-chao-brazilian-steakhouse-san-jose', 'https://www.opentable.com/il-fornaio-burlingame', 'https://www.opentable.com/prelude', 'https://www.opentable.com/yank-sing-rincon-center', 'https://www.opentable.com/r/the-shuckery-petaluma', 'https://www.opentable.com/dio-deka', 'https://www.opentable.com/epic-steak-fka-epic-roasthouse', 'https://www.opentable.com/chapeau', 'https://www.opentable.com/celadon', 'https://www.opentable.com/belga', 'https://www.opentable.com/esin-restaurant-and-bar', 'https://www.opentable.com/kitchen-istanbul', 'https://www.opentable.com/left-bank-santana-row', 'https://www.opentable.com/sasa', 'https://www.opentable.com/black-angus-steakhouse-brentwood', 'https://www.opentable.com/italian-colors', 'https://www.opentable.com/garden-court', 'https://www.opentable.com/kyoto-palace-restaurant', 'https://www.opentable.com/the-basin', 'https://www.opentable.com/r/opa-willow-glen-san-jose', 'https://www.opentable.com/black-angus-steakhouse-pleasant-hill', 'https://www.opentable.com/mayfield-bakery-and-cafe', 'https://www.opentable.com/torc', 'https://www.opentable.com/r/molina-restaurant-mill-valley', 'https://www.opentable.com/forbes-mill-steakhouse-danville', 'https://www.opentable.com/nm-cafe-at-neiman-marcus-palo-alto', 'https://www.opentable.com/r/incontro-danville', 'https://www.opentable.com/prospect', 'https://www.opentable.com/pacific-catch-campbell', 'https://www.opentable.com/a16-san-francisco', 'https://www.opentable.com/parada-peruvian-kitchen', 'https://www.opentable.com/the-plumed-horse', 'https://www.opentable.com/la-mar-cebicheria-peruana', 'https://www.opentable.com/balboa-cafe', 'https://www.opentable.com/bistro-aix-sf', 'https://www.opentable.com/casa-orinda', 'https://www.opentable.com/willard-hicks', 'https://www.opentable.com/trabocco', 'https://www.opentable.com/la-nebbia-restaurant', 'https://www.opentable.com/town-hall-san-francisco', 'https://www.opentable.com/r/farm-and-vine-burlingame', 'https://www.opentable.com/la-fondue', 'https://www.opentable.com/pacific-catch-mountain-view', 'https://www.opentable.com/kin-khao', 'https://www.opentable.com/ajanta-restaurant', 'https://www.opentable.com/dry-creek-grill', 'https://www.opentable.com/joya-restaurant-and-lounge', 'https://www.opentable.com/zazie', 'https://www.opentable.com/the-melting-pot-larkspur', 'https://www.opentable.com/the-spinnaker-sausalito', 'https://www.opentable.com/salt-house', 'https://www.opentable.com/hopmonk-tavern-novato', 'https://www.opentable.com/r/speisekammer-alameda', 'https://www.opentable.com/murray-circle', 'https://www.opentable.com/hops-and-hominy', 'https://www.opentable.com/heirloom-cafe', 'https://www.opentable.com/ravens-restaurant-stanford-inn-by-the-sea', 'https://www.opentable.com/il-fornaio-corte-madera', 'https://www.opentable.com/serpentine', 'https://www.opentable.com/mamma-taninos-ristorante', 'https://www.opentable.com/flora-oakland', 'https://www.opentable.com/piazza-dangelo', 'https://www.opentable.com/bistro-jeanty', 'https://www.opentable.com/fiorella', 'https://www.opentable.com/baci-cafe-and-wine-bar', 'https://www.opentable.com/r/drakes-sonoma-coast-kitchen-bodega-bay', 'https://www.opentable.com/parkside-grill', 'https://www.opentable.com/station-house-cafe', 'https://www.opentable.com/r/reve-lafayette', 'https://www.opentable.com/black-angus-steakhouse-sunnyvale', 'https://www.opentable.com/big-4-restaurant', 'https://www.opentable.com/hana-japanese-restaurant', 'https://www.opentable.com/the-peasant-and-the-pear', 'https://www.opentable.com/venticello', 'https://www.opentable.com/bistro-don-giovanni-napa', 'https://www.opentable.com/left-bank-larkspur', 'https://www.opentable.com/il-fornaio-palo-alto', 'https://www.opentable.com/bar-tartine', 'https://www.opentable.com/trattoria-contadina', 'https://www.opentable.com/jardiniere', 'https://www.opentable.com/la-note-restaurant-provencal', 'https://www.opentable.com/west-side-grill-gilroy', 'https://www.opentable.com/bobos', 'https://www.opentable.com/parcel-104', 'https://www.opentable.com/r/rambler-san-francisco', 'https://www.opentable.com/el-dorado-kitchen', 'https://www.opentable.com/allegro-romano', 'https://www.opentable.com/penrose', 'https://www.opentable.com/paradiso-san-leandro', 'https://www.opentable.com/left-bank-menlo-park', 'https://www.opentable.com/mochica', 'https://www.opentable.com/caffe-delle-stelle', 'https://www.opentable.com/pasta-moon', 'https://www.opentable.com/duende', 'https://www.opentable.com/patrona-ukiah', 'https://www.opentable.com/cafe-bistro-nordstrom-palo-alto', 'https://www.opentable.com/prima-ristorante', 'https://www.opentable.com/piatti-mill-valley', 'https://www.opentable.com/goose-and-gander', 'https://www.opentable.com/black-angus-steakhouse-san-lorenzo', 'https://www.opentable.com/townhouse-bar-and-grill', 'https://www.opentable.com/aventine-glen-ellen', 'https://www.opentable.com/lb-steak-santana-row', 'https://www.opentable.com/corners-tavern', 'https://www.opentable.com/ristorante-allegria', 'https://www.opentable.com/pacific-catch-san-mateo', 'https://www.opentable.com/colibri-mexican-bistro', 'https://www.opentable.com/birks', 'https://www.opentable.com/maccallum-house', 'https://www.opentable.com/zut-tavern', 'https://www.opentable.com/commonwealth-san-francisco', 'https://www.opentable.com/metro-lafayette', 'https://www.opentable.com/pacific-catch-corte-madera', 'https://www.opentable.com/oswald', 'https://www.opentable.com/sakoon', 'https://www.opentable.com/ace-wasabis-rock-n-roll-sushi', 'https://www.opentable.com/central-market', 'https://www.opentable.com/il-fornaio-san-jose', 'https://www.opentable.com/amber-india-mountain-view', 'https://www.opentable.com/assemble', 'https://www.opentable.com/sante-at-the-fairmont-sonoma-mission-inn', 'https://www.opentable.com/zabu-zabu-san-mateo', 'https://www.opentable.com/mortons-the-steakhouse-san-francisco', 'https://www.opentable.com/boxing-room', 'https://www.opentable.com/moss-beach-distillery', 'https://www.opentable.com/john-ash-and-co', 'https://www.opentable.com/scomas-restaurant', 'https://www.opentable.com/r/three-restaurant-and-bar-san-mateo', 'https://www.opentable.com/simply-fondue-livermore', 'https://www.opentable.com/the-cooperage', 'https://www.opentable.com/scratch-mtn-view', 'https://www.opentable.com/archetype', 'https://www.opentable.com/aster', 'https://www.opentable.com/yankee-pier-lafayette', 'https://www.opentable.com/a16-rockridge', 'https://www.opentable.com/ca-bianca', 'https://www.opentable.com/massimo-ristorante', 'https://www.opentable.com/sociale', 'https://www.opentable.com/seiya', 'https://www.opentable.com/la-costanera', 'https://www.opentable.com/lv-mar', 'https://www.opentable.com/zephyr-grill-and-bar', 'https://www.opentable.com/buca-di-beppo-palo-alto', 'https://www.opentable.com/straits-restaurant-santana-row', 'https://www.opentable.com/blue-stove-nordstrom-the-village-at-corte-madera', 'https://www.opentable.com/aatxe', 'https://www.opentable.com/farallon', 'https://www.opentable.com/meritage-at-the-claremont', 'https://www.opentable.com/pacific-catch-dublin', 'https://www.opentable.com/the-grill-on-the-alley-san-jose', 'https://www.opentable.com/nola', 'https://www.opentable.com/piccino', 'https://www.opentable.com/camino', 'https://www.opentable.com/gioia-pizzeria', 'https://www.opentable.com/blackhawk-grille', 'https://www.opentable.com/range', 'https://www.opentable.com/the-cavalier', 'https://www.opentable.com/pappo', 'https://www.opentable.com/firefly-restaurant', 'https://www.opentable.com/a-caprice', 'https://www.opentable.com/vin-santo', 'https://www.opentable.com/willow-street-wood-fired-pizza-los-gatos', 'https://www.opentable.com/ozumo-san-francisco', 'https://www.opentable.com/trader-vics-emeryville', 'https://www.opentable.com/scotts-restaurant', 'https://www.opentable.com/mountain-house-woodside', 'https://www.opentable.com/amber-india-santana-row', 'https://www.opentable.com/skates-on-the-bay', 'https://www.opentable.com/hollins-house-pasatiempo-golf-club', 'https://www.opentable.com/causwells', 'https://www.opentable.com/juhu-beach-club', 'https://www.opentable.com/vault-164', 'https://www.opentable.com/pican', 'https://www.opentable.com/viognier', 'https://www.opentable.com/spqr-san-francisco', 'https://www.opentable.com/quince-restaurant-san-francisco', 'https://www.opentable.com/rn74', 'https://www.opentable.com/r/tai-pan-palo-alto', 'https://www.opentable.com/bushido', 'https://www.opentable.com/bella-trattoria-italiana', 'https://www.opentable.com/garre-cafe', 'https://www.opentable.com/wildfox', 'https://www.opentable.com/rangoon-ruby-burmese-cuisine-san-carlos', 'https://www.opentable.com/paul-martins-american-grill-san-mateo', 'https://www.opentable.com/54-mint', 'https://www.opentable.com/little-star-pizza', 'https://www.opentable.com/burma-ruby', 'https://www.opentable.com/bertoluccis', 'https://www.opentable.com/hilltop-1892', 'https://www.opentable.com/pub-republic', 'https://www.opentable.com/r/umami-burger-palo-alto', 'https://www.opentable.com/old-bus-tavern', 'https://www.opentable.com/iyasare', 'https://www.opentable.com/maxs-opera-cafe-of-palo-alto', 'https://www.opentable.com/jasons-restaurant', 'https://www.opentable.com/otoro-sushi', 'https://www.opentable.com/rock-bottom-brewery-restaurant-san-jose', 'https://www.opentable.com/cocotte-san-francisco', 'https://www.opentable.com/crab-house-at-pier-39', 'https://www.opentable.com/mccormick-and-schmicks-seafood-san-jose', 'https://www.opentable.com/mokutanya-yakitori-charcoal', 'https://www.opentable.com/xanh-restaurant', 'https://www.opentable.com/roys-san-francisco', 'https://www.opentable.com/michael-mina-restaurant', 'https://www.opentable.com/terra-mia', 'https://www.opentable.com/wild-goat-bistro-petaluma', 'https://www.opentable.com/pane-e-vino-trattoria', 'https://www.opentable.com/scotts-seafood-oakland', 'https://www.opentable.com/ideale', 'https://www.opentable.com/mankas-steakhouse', 'https://www.opentable.com/the-perennial', 'https://www.opentable.com/hazel-occidental', 'https://www.opentable.com/r/havana-restaurant-walnut-creek', 'https://www.opentable.com/plaj', 'https://www.opentable.com/dona-tomas', 'https://www.opentable.com/uchiwa-ramen', 'https://www.opentable.com/vivace-belmont', 'https://www.opentable.com/la-marcha', 'https://www.opentable.com/r/lao-table-san-francisco', 'https://www.opentable.com/paul-martins-american-grill-mountain-view', 'https://www.opentable.com/danas', 'https://www.opentable.com/donato-enoteca', 'https://www.opentable.com/rosa-mexicano-san-francisco', 'https://www.opentable.com/kingfish', 'https://www.opentable.com/lark-creek', 'https://www.opentable.com/soif-wine-bar-restaurant', 'https://www.opentable.com/walter-hansel-wine-bistro', 'https://www.opentable.com/its-italia', 'https://www.opentable.com/shana-thai-restaurant', 'https://www.opentable.com/kingston-11', 'https://www.opentable.com/steamers-grillhouse', 'https://www.opentable.com/locanda-ravello', 'https://www.opentable.com/wine-cellar-restaurant', 'https://www.opentable.com/vin-antico', 'https://www.opentable.com/vaso-azzurro', 'https://www.opentable.com/horatios', 'https://www.opentable.com/cetrella', 'https://www.opentable.com/miramar-beach-restaurant', 'https://www.opentable.com/r/anchor-and-hope-san-francisco', 'https://www.opentable.com/soi4-bangkok-eatery', 'https://www.opentable.com/eddie-papas-american-hangout', 'https://www.opentable.com/portola-kitchen', 'https://www.opentable.com/the-star', 'https://www.opentable.com/kakui', 'https://www.opentable.com/claremont-lobby-lounge-and-bar', 'https://www.opentable.com/roka-akor-san-francisco', 'https://www.opentable.com/cafe-rouge', 'https://www.opentable.com/the-vans-on-the-hill', 'https://www.opentable.com/state-room-san-rafael', 'https://www.opentable.com/risibisi', 'https://www.opentable.com/faultline-brewing-company', 'https://www.opentable.com/r/loma-brewing-company-los-gatos', 'https://www.opentable.com/madrona-manor', 'https://www.opentable.com/r/corridor-san-francisco', 'https://www.opentable.com/perrys-design-center', 'https://www.opentable.com/lb-steak-menlo-park', 'https://www.opentable.com/hawker-fare-sf', 'https://www.opentable.com/rickeys', 'https://www.opentable.com/r/el-torito-san-leandro', 'https://www.opentable.com/locanda-positano-san-carlos', 'https://www.opentable.com/morimoto-napa', 'https://www.opentable.com/espetus-churrascaria-san-mateo', 'https://www.opentable.com/fogo-de-chao-brazilian-steakhouse-san-francisco', 'https://www.opentable.com/25-lusk', 'https://www.opentable.com/pacific-catch-sunset-district', 'https://www.opentable.com/r/umami-burger-marina-district-san-francisco', 'https://www.opentable.com/massimos-fremont', 'https://www.opentable.com/r/gourmet-au-bay-bodega-bay', 'https://www.opentable.com/hayes-street-grill', 'https://www.opentable.com/lucca-bar-and-grill', 'https://www.opentable.com/oenotri', 'https://www.opentable.com/cetrella-los-altos', 'https://www.opentable.com/r/lima-concord', 'https://www.opentable.com/brix', 'https://www.opentable.com/palm-house', 'https://www.opentable.com/r/lavier-latin-fusion-san-rafael', 'https://www.opentable.com/r/gia-ristorante-italiano-larkspur', 'https://www.opentable.com/k-and-l-bistro', 'https://www.opentable.com/arcadia', 'https://www.opentable.com/tsunami-panhandle', 'https://www.opentable.com/sutros-at-the-cliff-house', 'https://www.opentable.com/le-garage', 'https://www.opentable.com/longbranch-saloon', 'https://www.opentable.com/crush-ukiah', 'https://www.opentable.com/sino-restaurant-and-lounge', 'https://www.opentable.com/osteria-palo-alto', 'https://www.opentable.com/via-uno-cucina-italiana-and-bar', 'https://www.opentable.com/marzano', 'https://www.opentable.com/rasoi-burlingame', 'https://www.opentable.com/doppio-zero', 'https://www.opentable.com/r/the-last-word-livermore', 'https://www.opentable.com/fontanas-italian', 'https://www.opentable.com/fang', 'https://www.opentable.com/giannis-italian-bistro', 'https://www.opentable.com/wences-restaurant', 'https://www.opentable.com/au-midi-restaurant-and-bistrot', 'https://www.opentable.com/black-angus-steakhouse-vallejo', 'https://www.opentable.com/la-toque-westin-napa', 'https://www.opentable.com/r/la-collina-millbrae', 'https://www.opentable.com/the-stinking-rose-san-francisco', 'https://www.opentable.com/tuba-restaurant', 'https://www.opentable.com/rangoon-ruby-burmese-cuisine-belmont', 'https://www.opentable.com/scalas-bistro', 'https://www.opentable.com/frantoio-ristorante', 'https://www.opentable.com/bar-agricole', 'https://www.opentable.com/sens-restaurant', 'https://www.opentable.com/la-sen-bistro', 'https://www.opentable.com/florio', 'https://www.opentable.com/poesia', 'https://www.opentable.com/carpe-diem-wine-bar', 'https://www.opentable.com/piqueos', 'https://www.opentable.com/benissimo-ristorante-and-bar', 'https://www.opentable.com/chotto', 'https://www.opentable.com/5a5-steak-lounge', 'https://www.opentable.com/bocanova', 'https://www.opentable.com/mela-tandoori-kitchen', 'https://www.opentable.com/r/la-pizzeria-campbell', 'https://www.opentable.com/creola', 'https://www.opentable.com/scotts-seafood-san-jose', 'https://www.opentable.com/vanessas-bistro-2', 'https://www.opentable.com/cafe-torre', 'https://www.opentable.com/alamo-square-seafood-grill', 'https://www.opentable.com/r/aroy-thai-bistro-palo-alto', 'https://www.opentable.com/calavera-mexican-kitchen-and-agave-bar', 'https://www.opentable.com/hawker-fare', 'https://www.opentable.com/the-park-bistro-and-bar', 'https://www.opentable.com/brasswood-bar-and-kitchen', 'https://www.opentable.com/keiko-a-nob-hill', 'https://www.opentable.com/chalkboard-healdsburg', 'https://www.opentable.com/r/double-barrel-wine-bar-livermore', 'https://www.opentable.com/fonda', 'https://www.opentable.com/hopmonk-tavern', 'https://www.opentable.com/saffron-indian-bistro', 'https://www.opentable.com/luna-blu-tiburon', 'https://www.opentable.com/r/silverado-resort-and-spa-christmas-buffet-in-the-grand-ballroom-napa', 'https://www.opentable.com/leatherneck-steakhouse', 'https://www.opentable.com/la-toscana-ristorante', 'https://www.opentable.com/isa', 'https://www.opentable.com/delizie', 'https://www.opentable.com/baci-bistro-and-bar', 'https://www.opentable.com/sushi-omakase', 'https://www.opentable.com/eikos', 'https://www.opentable.com/palacio', 'https://www.opentable.com/three-seasons-palo-alto', 'https://www.opentable.com/julias-at-the-berkeley-city-club', 'https://www.opentable.com/blue-plate', 'https://www.opentable.com/menlo-grill-bistro-and-bar', 'https://www.opentable.com/the-farmers-union', 'https://www.opentable.com/r/umami-burger-soma-san-francisco', 'https://www.opentable.com/r/palmers-tavern-san-francisco', 'https://www.opentable.com/maxs-restaurant-and-bar-of-burlingame', 'https://www.opentable.com/the-fly-trap', 'https://www.opentable.com/aperto', 'https://www.opentable.com/r/the-restaurant-at-cia-copia-napa', 'https://www.opentable.com/r/saha-berkeley', 'https://www.opentable.com/divino-belmont', 'https://www.opentable.com/r/barrel-head-brewhouse-san-francisco', 'https://www.opentable.com/gold-mirror-italian-restaurant', 'https://www.opentable.com/r/il-postale-sunnyvale', 'https://www.opentable.com/ijji-sushi', 'https://www.opentable.com/roti-indian-bistro-san-francisco', 'https://www.opentable.com/amber-dhara', 'https://www.opentable.com/daily-grill-san-francisco', 'https://www.opentable.com/izakaya-kou', 'https://www.opentable.com/marketbar', 'https://www.opentable.com/crystal-jade-jiang-nan', 'https://www.opentable.com/indo-restaurant-and-lounge', 'https://www.opentable.com/cafe-de-la-presse', 'https://www.opentable.com/primavera-ristorante', 'https://www.opentable.com/straits-restaurant-burlingame', 'https://www.opentable.com/agenzen-japanese-cuisine', 'https://www.opentable.com/r/nightbird-san-francisco', 'https://www.opentable.com/r/orenchi-beyond-san-francisco', 'https://www.opentable.com/fringale', 'https://www.opentable.com/beach-chalet-brewery-and-restaurant', 'https://www.opentable.com/haven-oakland', 'https://www.opentable.com/vanessas-bistro', 'https://www.opentable.com/benihana-san-francisco', 'https://www.opentable.com/barones-restaurant', 'https://www.opentable.com/the-brass-door', 'https://www.opentable.com/don-antonio-trattoria', 'https://www.opentable.com/barlago-italian-kitchen', 'https://www.opentable.com/thaiphoon-restaurant', 'https://www.opentable.com/r/crocodile-petaluma', 'https://www.opentable.com/lago-di-como', 'https://www.opentable.com/bistrot-vida', 'https://www.opentable.com/ristorante-don-giovanni-mountain-view', 'https://www.opentable.com/kiji-sushi-bar-and-cuisine', 'https://www.opentable.com/nemea', 'https://www.opentable.com/r/willow-street-wood-fired-pizza-san-jose', 'https://www.opentable.com/r/osteria-san-francisco', 'https://www.opentable.com/macarthur-park', 'https://www.opentable.com/iron-gate', 'https://www.opentable.com/pier-market-seafood-restaurant-pier-39-sf', 'https://www.opentable.com/lupa-trattoria', 'https://www.opentable.com/pasta-primavera-cafe-and-bar-walnut-creek', 'https://www.opentable.com/mayo-reserve-room-mayo-family-winery', 'https://www.opentable.com/aslams-rasoi', 'https://www.opentable.com/r/galpao-gaucho-napa', 'https://www.opentable.com/sanderlings-seascape-resort', 'https://www.opentable.com/mccormick-and-kuletos-seafood-restaurant', 'https://www.opentable.com/stanfords-walnut-creek', 'https://www.opentable.com/sams-chowder-house-palo-alto', 'https://www.opentable.com/park-chalet', 'https://www.opentable.com/rocca-ristorante', 'https://www.opentable.com/888-ristorante-italiano', 'https://www.opentable.com/ozumo-oakland', 'https://www.opentable.com/belcampo-larkspur', 'https://www.opentable.com/arguello', 'https://www.opentable.com/kimono-restaurant', 'https://www.opentable.com/salute-e-vita-ristorante', 'https://www.opentable.com/jeanne-darc-cornell-hotel-de-france', 'https://www.opentable.com/sunol-ridge-restaurant-and-bar', 'https://www.opentable.com/willis-wine-bar', 'https://www.opentable.com/r/patxis-marina-san-francisco', 'https://www.opentable.com/r/pausa-san-mateo', 'https://www.opentable.com/farmhouse-inn-and-restaurant', 'https://www.opentable.com/restaurant/profile/273535?p=2&sd=2017-02-12%2019%3A00', 'https://www.opentable.com/r/california-fresh-cooking-class-menlo-park', 'https://www.opentable.com/r/kinjo-san-francisco', 'https://www.opentable.com/r/messob-ethiopian-restaurant-oakland', 'https://www.opentable.com/r/on-fire-pizza-san-ramon', 'https://www.opentable.com/r/canasta-kitchen-concord', 'https://www.opentable.com/r/gatehouse-restaurant-saint-helena', 'https://www.opentable.com/r/alamo-grill-alamo', 'https://www.opentable.com/r/the-wine-project-san-carlos', 'https://www.opentable.com/r/dan-gordons-palo-alto', 'https://www.opentable.com/r/persephone-restaurant-aptos', 'https://www.opentable.com/restaurant/profile/349105?p=2&sd=2017-02-12%2019%3A00', 'https://www.opentable.com/r/lucias-berkeley', 'https://www.opentable.com/restaurant/profile/349255?p=2&sd=2017-02-12%2019%3A00', 'https://www.opentable.com/restaurant/profile/349282?p=2&sd=2017-02-12%2019%3A00', 'https://www.opentable.com/restaurant/profile/349378?p=2&sd=2017-02-12%2019%3A00', 'https://www.opentable.com/restaurant/profile/349942?p=2&sd=2017-02-12%2019%3A00', 'https://www.opentable.com/restaurant/profile/349972?p=2&sd=2017-02-12%2019%3A00', 'https://www.opentable.com/restaurant/profile/350086?p=2&sd=2017-02-12%2019%3A00', 'https://www.opentable.com/r/swaad-indian-cuisine-san-jose', 'https://www.opentable.com/r/the-sweet-onion-waynesville', 'https://www.opentable.com/sapore-italiano', 'https://www.opentable.com/limon-rotisserie-valencia', 'https://www.opentable.com/the-cantina-mill-valley', 'https://www.opentable.com/limon-rotisserie-van-ness', 'https://www.opentable.com/akasaka-sushi', 'https://www.opentable.com/gourmet-express', 'https://www.opentable.com/r/boot-and-shoe-service-oakland', 'https://www.opentable.com/r/kells-irish-restaurant-san-francisco', 'https://www.opentable.com/r/casa-azteca-milpitas', 'https://www.opentable.com/r/kobe-japanese-cuisine-and-bar-foster-city', 'https://www.opentable.com/r/goji-kitchen-santa-rosa', 'https://www.opentable.com/r/vina-enoteca-palo-alto', 'https://www.opentable.com/r/les-bizous-palo-alto', 'https://www.opentable.com/r/zaytoon-albany', 'https://www.opentable.com/fog-city', 'https://www.opentable.com/per-diem', 'https://www.opentable.com/vitos-trattoria', 'https://www.opentable.com/piatti-santa-clara', 'https://www.opentable.com/waxmans', 'https://www.opentable.com/rangoon-ruby-burmese-cuisine-burlingame', 'https://www.opentable.com/lure-and-till', 'https://www.opentable.com/yuzuki-japanese-eatery-fka-izakaya-yuzuki', 'https://www.opentable.com/michel', 'https://www.opentable.com/r/izakaya-ginji-san-mateo', 'https://www.opentable.com/pear-street-bistro', 'https://www.opentable.com/a-bellagio', 'https://www.opentable.com/farmer-brown', 'https://www.opentable.com/rosys-at-the-beach', 'https://www.opentable.com/zen-sushi-bistro', 'https://www.opentable.com/de-la-torres-trattoria', 'https://www.opentable.com/angele-restaurant-and-bar', 'https://www.opentable.com/mistral-restaurant-and-bar-redwood-city', 'https://www.opentable.com/r/berevino-italian-cucina-dublin', 'https://www.opentable.com/lucetis-on-25th-avenue', 'https://www.opentable.com/destino', 'https://www.opentable.com/maxs-of-redwood-city', 'https://www.opentable.com/oasis-grille', 'https://www.opentable.com/bacco-ristorante', 'https://www.opentable.com/don-antonio-larkspur', 'https://www.opentable.com/the-sausage-factory', 'https://www.opentable.com/bistro-10un', 'https://www.opentable.com/otaez-mexican-restaurant-alameda', 'https://www.opentable.com/osha-thai-3rd-street', 'https://www.opentable.com/kincaids-bayhouse-oakland', 'https://www.opentable.com/gabriella-cafe', 'https://www.opentable.com/chalet-basque', 'https://www.opentable.com/sessions-at-the-presidio', 'https://www.opentable.com/thai-time-restaurant-and-bar', 'https://www.opentable.com/lion-and-compass', 'https://www.opentable.com/vero', 'https://www.opentable.com/restaurant/profile/342436?p=2&sd=2017-02-12%2019%3A00', 'https://www.opentable.com/restaurant/profile/343621?p=2&sd=2017-02-12%2019%3A00', 'https://www.opentable.com/chambers-eat-and-drink', 'https://www.opentable.com/bistro-29', 'https://www.opentable.com/r/zaiqa-restaurant-hercules', 'https://www.opentable.com/cafe-eugene', 'https://www.opentable.com/la-lanterna-ristorante', 'https://www.opentable.com/r/luttickens-after-5-menlo-park', 'https://www.opentable.com/firehouse-bistro', 'https://www.opentable.com/tres-sf-fka-tres-agaves', 'https://www.opentable.com/mezcal-san-jose', 'https://www.opentable.com/r/cascade-bar-and-grill-at-costanoa-pescadero', 'https://www.opentable.com/mezzaluna-half-moon-bay', 'https://www.opentable.com/osmanthus', 'https://www.opentable.com/r/scopo-divino-san-francisco', 'https://www.opentable.com/r/sinaloa-cafe-morgan-hill', 'https://www.opentable.com/viva-neighborhood-eatery-of-los-gatos', 'https://www.opentable.com/hults', 'https://www.opentable.com/montesacro-pinseria', 'https://www.opentable.com/sabio-on-main', 'https://www.opentable.com/r/black-cat-san-francisco', 'https://www.opentable.com/gintei', 'https://www.opentable.com/galata-bistro', 'https://www.opentable.com/r/bella-ristorante-concord', 'https://www.opentable.com/spiazzo-ristorante', 'https://www.opentable.com/faz-sunnyvale', 'https://www.opentable.com/sakoon-fremont', 'https://www.opentable.com/capers', 'https://www.opentable.com/i-prive-sushi-sake-spirits', 'https://www.opentable.com/restaurant/profile/343714?p=2&sd=2017-02-12%2019%3A00', 'https://www.opentable.com/wine-and-waffles', 'https://www.opentable.com/r/yucca-de-lac-palo-alto', 'https://www.opentable.com/top-of-the-market-san-mateo', 'https://www.opentable.com/r/moodees-indian-cuisine-san-francisco', 'https://www.opentable.com/r/rodney-strong-vineyards-healdsburg', 'https://www.opentable.com/chianti-reserve', 'https://www.opentable.com/r/the-alembic-san-francisco', 'https://www.opentable.com/rustic-tavern', 'https://www.opentable.com/abc-seafood-foster-city', 'https://www.opentable.com/blowfish-sushi-san-jose', 'https://www.opentable.com/r/ghazal-indian-cuisine-oakland', 'https://www.opentable.com/r/shirasoni-alameda', 'https://www.opentable.com/artisan-lafayette', 'https://www.opentable.com/spasso-san-carlos', 'https://www.opentable.com/calzones', 'https://www.opentable.com/canela-bistro-and-wine-bar', 'https://www.opentable.com/mission-beach-cafe', 'https://www.opentable.com/yeti-indian-cuisine-restaurant', 'https://www.opentable.com/r/thai-square-cupertino', 'https://www.opentable.com/desco', 'https://www.opentable.com/3rd-cousin', 'https://www.opentable.com/glen-ellen-inn-oyster-grill-and-martini-bar', 'https://www.opentable.com/servino-ristorante', 'https://www.opentable.com/pastas-trattoria', 'https://www.opentable.com/fiesta-vallarta', 'https://www.opentable.com/american-kitchen', 'https://www.opentable.com/bear-republic-brewing-company', 'https://www.opentable.com/i-gatti', 'https://www.opentable.com/r/da-flora-san-francisco', 'https://www.opentable.com/revival-bar-and-kitchen', 'https://www.opentable.com/gravity-bistro-and-wine-bar', 'https://www.opentable.com/hecho-castro', 'https://www.opentable.com/r/mosu-san-francisco', 'https://www.opentable.com/stone-korean-kitchen', 'https://www.opentable.com/lalimes', 'https://www.opentable.com/bourbon-and-beef', 'https://www.opentable.com/r/cafe-florian-foster-city', 'https://www.opentable.com/bourbon-pub', 'https://www.opentable.com/blowfish-sushi-sf', 'https://www.opentable.com/baker-street-bistro', 'https://www.opentable.com/r/stone-stew-san-jose', 'https://www.opentable.com/alegrias-food-from-spain', 'https://www.opentable.com/r/abigails-moroccan-cuisine-alameda', 'https://www.opentable.com/fusebox', 'https://www.opentable.com/r/dinahs-poolside-restaurant-palo-alto', 'https://www.opentable.com/r/the-fishermans-taverna-half-moon-bay', 'https://www.opentable.com/lungomare', 'https://www.opentable.com/nihon-whisky-lounge', 'https://www.opentable.com/namaste-madreas-cuisine', 'https://www.opentable.com/oso', 'https://www.opentable.com/espetus-churrascaria-san-francisco', 'https://www.opentable.com/homestead', 'https://www.opentable.com/market-st-helena', 'https://www.opentable.com/bella-saratoga', 'https://www.opentable.com/restaurant-301-eureka', 'https://www.opentable.com/tribune-tavern', 'https://www.opentable.com/by-th-bucket-bar-and-grill', 'https://www.opentable.com/trou-normand', 'https://www.opentable.com/piacere', 'https://www.opentable.com/cucina-venti', 'https://www.opentable.com/neumanali', 'https://www.opentable.com/buon-gusto', 'https://www.opentable.com/park-grill-le-meridien-san-francisco', 'https://www.opentable.com/the-restaurant-at-russian-river-vineyards-fka-corks-at-russian-river-vineyards', 'https://www.opentable.com/uva-enoteca', 'https://www.opentable.com/hopmonk-tavern-sonoma', 'https://www.opentable.com/e-and-o-kitchen-and-bar', 'https://www.opentable.com/lucy-restaurant-and-bar-at-bardessono', 'https://www.opentable.com/depot-hotel-restaurant', 'https://www.opentable.com/spoonbar-h2hotel', 'https://www.opentable.com/pino-alto-restaurant-cabrillo-college', 'https://www.opentable.com/r/east-restaurant-mountain-view', 'https://www.opentable.com/jersey-restaurant', 'https://www.opentable.com/basil-canteen', 'https://www.opentable.com/r/sukho-thai-oakland', 'https://www.opentable.com/baci-cafe-blackhawk', 'https://www.opentable.com/perrys-embarcadero', 'https://www.opentable.com/vespucci-ristorante-italiano', 'https://www.opentable.com/crouching-tiger-restaurant', 'https://www.opentable.com/chez-tj', 'https://www.opentable.com/saiwalks-vietnamese-street-food', 'https://www.opentable.com/shiok-singapore-kitchen', 'https://www.opentable.com/restaurant/profile/342568?p=2&sd=2017-02-12%2019%3A00', 'https://www.opentable.com/perrys-union-street', 'https://www.opentable.com/cafe-jolie', 'https://www.opentable.com/central-park-bistro', 'https://www.opentable.com/r/miminashi-napa', 'https://www.opentable.com/ristorante-bella-vita-los-altos', 'https://www.opentable.com/r/mint-and-basil-milpitas', 'https://www.opentable.com/rendez-vous-cafe-bistro', 'https://www.opentable.com/r/brittany-crepes-berkeley', 'https://www.opentable.com/franciscan-crab-restaurant', 'https://www.opentable.com/north-india-restaurant', 'https://www.opentable.com/parlour-oakland', 'https://www.opentable.com/press-club', 'https://www.opentable.com/r/kendall-jackson-wine-estate-and-gardens-fulton', 'https://www.opentable.com/r/red-chillies-milpitas', 'https://www.opentable.com/cleos-brazilian-steakhouse-and-churrascaria', 'https://www.opentable.com/evangeline-calistoga', 'https://www.opentable.com/sams-grill-and-seafood-restaurant', 'https://www.opentable.com/fable', 'https://www.opentable.com/the-trident', 'https://www.opentable.com/garcon-san-francisco', 'https://www.opentable.com/r/prabh-indian-kitchen-mill-valley', 'https://www.opentable.com/cafe-bistro-nordstrom-san-francisco-centre', 'https://www.opentable.com/r/nasch-los-gatos', 'https://www.opentable.com/meadowood-the-grill', 'https://www.opentable.com/r/the-fat-lady-bar-and-restaurant-oakland', 'https://www.opentable.com/r/doppio-zero-cupertino', 'https://www.opentable.com/zazu-kitchen-and-farm', 'https://www.opentable.com/la-finestra-ristorante-lafayette-bay-area', 'https://www.opentable.com/r/cherry-sushi-santa-clara', 'https://www.opentable.com/r/the-conservatory-the-ritz-carlton-half-moon-bay', 'https://www.opentable.com/campton-place', 'https://www.opentable.com/osso-steakhouse', 'https://www.opentable.com/mandaloun', 'https://www.opentable.com/the-old-clam-house', 'https://www.opentable.com/tavares', 'https://www.opentable.com/arya-global-cuisine', 'https://www.opentable.com/hanna', 'https://www.opentable.com/r/our-house-san-jose', 'https://www.opentable.com/kronnerburger', 'https://www.opentable.com/paragon-restaurant-and-bar-san-francisco', 'https://www.opentable.com/r/mint-and-basil-san-jose', 'https://www.opentable.com/spalti', 'https://www.opentable.com/ethiopia-restaurant', 'https://www.opentable.com/bistro-boudin', 'https://www.opentable.com/west-park-bistro', 'https://www.opentable.com/la-folie', 'https://www.opentable.com/bijou-restaurant-and-bar', 'https://www.opentable.com/sausalito-seahorse', 'https://www.opentable.com/alys-on-main', 'https://www.opentable.com/dobbs-ferry-restaurant', 'https://www.opentable.com/the-pullman-kitchen-santa-rosa', 'https://www.opentable.com/lasalette-restaurant', 'https://www.opentable.com/roses-cafe', 'https://www.opentable.com/farm-at-the-carneros-inn', 'https://www.opentable.com/r/lotus-thai-cuisine-oakland', 'https://www.opentable.com/nicks-cove', 'https://www.opentable.com/portobello-grill', 'https://www.opentable.com/broadway-grill', 'https://www.opentable.com/aquarius-dream-inn', 'https://www.opentable.com/momos', 'https://www.opentable.com/quinns-lighthouse-restaurant-and-pub', 'https://www.opentable.com/r/wasabi-tapas-capitola', 'https://www.opentable.com/r/ichi-sushi-san-francisco', 'https://www.opentable.com/faz-danville', 'https://www.opentable.com/southpaw-bbq', 'https://www.opentable.com/live-sushi-bar', 'https://www.opentable.com/frontier-spice-pleasanton', 'https://www.opentable.com/barcha', 'https://www.opentable.com/tannourine', 'https://www.opentable.com/chiantis-brentwood', 'https://www.opentable.com/park-balluchi', 'https://www.opentable.com/little-river-inn-restaurant', 'https://www.opentable.com/bourbon-steak-santa-clara', 'https://www.opentable.com/chianti-osteria', 'https://www.opentable.com/bambinos-ristorante', 'https://www.opentable.com/r/tigerlily-berkeley', 'https://www.opentable.com/r/monsoon-himalayan-cuisine-half-moon-bay', 'https://www.opentable.com/mango-on-main-thai-bistro', 'https://www.opentable.com/bluefin-japanese-restaurant', 'https://www.opentable.com/south-park-cafe', 'https://www.opentable.com/baonecci-ristorante', 'https://www.opentable.com/aurora-ristorante-italiano', 'https://www.opentable.com/johns-grill', 'https://www.opentable.com/my-china-sf', 'https://www.opentable.com/caffe-macaroni', 'https://www.opentable.com/grand-view', 'https://www.opentable.com/tamashisoul-sushi-bar', 'https://www.opentable.com/manzoni', 'https://www.opentable.com/r/finfine-berkeley', 'https://www.opentable.com/gold-coast-grill', 'https://www.opentable.com/taurinus-brazilian-steakhouse', 'https://www.opentable.com/r/kaiwa-sushi-walnut-creek', 'https://www.opentable.com/r/mancora-cebicheria-san-mateo', 'https://www.opentable.com/quattro-restaurant-and-bar-four-seasons-hotel', 'https://www.opentable.com/the-commissary', 'https://www.opentable.com/porterhouse', 'https://www.opentable.com/the-tipsy-pig', 'https://www.opentable.com/cafe-mare-italian-restaurant', 'https://www.opentable.com/the-matterhorn-swiss-restaurant', 'https://www.opentable.com/alfreds-steakhouse-sf', 'https://www.opentable.com/hoffmanns-grill-and-rotisserie', 'https://www.opentable.com/r/little-gem-san-francisco', 'https://www.opentable.com/harvest-table', 'https://www.opentable.com/r/cocoaplanet-tasting-room-sonoma', 'https://www.opentable.com/le-central', 'https://www.opentable.com/sonoma-grille-sonoma', 'https://www.opentable.com/il-fornaio-san-francisco', 'https://www.opentable.com/americano-restaurant-hotel-vitale', 'https://www.opentable.com/wine-kitchen', 'https://www.opentable.com/teskes-germania-restaurant', 'https://www.opentable.com/flight-fremont', 'https://www.opentable.com/nonnis-bistro', 'https://www.opentable.com/ruchi', 'https://www.opentable.com/schroeders', 'https://www.opentable.com/farina', 'https://www.opentable.com/r/bella-vita-family-bistro-fairfield', 'https://www.opentable.com/boulettes-larder-and-boulibar', 'https://www.opentable.com/estrellita-mexican-bistro-and-cantina', 'https://www.opentable.com/cafe-pro-bono', 'https://www.opentable.com/ristorante-milano', 'https://www.opentable.com/r/la-fontana-santa-clara', 'https://www.opentable.com/saffron-685-mediterranean-turkish-cuisine', 'https://www.opentable.com/r/mangia-mangia-albany', 'https://www.opentable.com/credo', 'https://www.opentable.com/running-rooster', 'https://www.opentable.com/r/deccan-spice-san-francisco', 'https://www.opentable.com/tsunami-mission-bay', 'https://www.opentable.com/marla-bakery', 'https://www.opentable.com/r/spettro-oakland', 'https://www.opentable.com/bluewater-bistro-and-bar', 'https://www.opentable.com/napa-general-store', 'https://www.opentable.com/le-colonial-san-francisco', 'https://www.opentable.com/myriad-gastro-pub', 'https://www.opentable.com/bombay-garden-san-mateo', 'https://www.opentable.com/seafood-peddler', 'https://www.opentable.com/precita-park-cafe', 'https://www.opentable.com/r/novy-san-francisco', 'https://www.opentable.com/clay-oven-indian-restaurant-west-portal', 'https://www.opentable.com/r/siduri-wine-lounge-healdsburg', 'https://www.opentable.com/home-made-kitchen-cafe-and-bakery', 'https://www.opentable.com/guaymas', 'https://www.opentable.com/r/quinua-south-petaluma', 'https://www.opentable.com/brannans-grill', 'https://www.opentable.com/cafe-lucia-healdsburg', 'https://www.opentable.com/r/leila-by-the-bay-hercules', 'https://www.opentable.com/r/buri-tara-thai-cuisine-foster-city', 'https://www.opentable.com/pearl-of-the-ocean', 'https://www.opentable.com/fast-food-francais', 'https://www.opentable.com/r/the-vestry-san-francisco', 'https://www.opentable.com/pier-23-cafe', 'https://www.opentable.com/the-dorian', 'https://www.opentable.com/la-fontaine-restaurant', 'https://www.opentable.com/cafe-artemis-campbell-ca', 'https://www.opentable.com/hog-and-rocks', 'https://www.opentable.com/beso-spanish-tapas-and-wine-bar', 'https://www.opentable.com/r/annar-afghan-hayward', 'https://www.opentable.com/healdsburg-shed', 'https://www.opentable.com/pezzellas-villa-napoli', 'https://www.opentable.com/r/best-of-burma-2-santa-rosa', 'https://www.opentable.com/tub-tim-corte-madera', 'https://www.opentable.com/urban-putt', 'https://www.opentable.com/anatolian-kitchen', 'https://www.opentable.com/district-oakland', 'https://www.opentable.com/amoura-restaurant', 'https://www.opentable.com/yeti-restaurant-santa-rosa', 'https://www.opentable.com/presidio-cafe-presidio-golf-course', 'https://www.opentable.com/mitsunobu', 'https://www.opentable.com/district-san-francisco', 'https://www.opentable.com/faz-san-jose', 'https://www.opentable.com/thirsty-bear', 'https://www.opentable.com/yanagi-sushi-and-grill', 'https://www.opentable.com/la-strada-ristorante-italiano', 'https://www.opentable.com/amarena', 'https://www.opentable.com/village-inn-and-restaurant', 'https://www.opentable.com/cafe-brioche', 'https://www.opentable.com/casa-robles-restaurant', 'https://www.opentable.com/bluestem-brasserie-sf', 'https://www.opentable.com/lemongrass-thai-restaurant-livermore', 'https://www.opentable.com/galeto-brazilian-steakhouse', 'https://www.opentable.com/r/sipan-peruvian-restaurant-and-bar-saratoga', 'https://www.opentable.com/north-beach-restaurant', 'https://www.opentable.com/bouche-san-francisco', 'https://www.opentable.com/angelas', 'https://www.opentable.com/rose-pistola', 'https://www.opentable.com/ristorante-amoroma', 'https://www.opentable.com/los-moles-san-rafael', 'https://www.opentable.com/r/wenzhou-fish-noodles-and-more-san-jose', 'https://www.opentable.com/catch-san-francisco', 'https://www.opentable.com/lincoln-park-wine-bar', 'https://www.opentable.com/54-mint-il-forno-walnut-creek', 'https://www.opentable.com/alta-ca', 'https://www.opentable.com/cioppinos', 'https://www.opentable.com/r/pasta-pelican-alameda', 'https://www.opentable.com/r/bistro-viz-san-anselmo', 'https://www.opentable.com/mangia-tutti', 'https://www.opentable.com/red-dog', 'https://www.opentable.com/r/viva-thai-bistro-cupertino', 'https://www.opentable.com/pinos-trattoria', 'https://www.opentable.com/hurleys-restaurant-and-bar', 'https://www.opentable.com/the-meadows-restaurant-at-redwood-canyon', 'https://www.opentable.com/r/smoke-berkeley', 'https://www.opentable.com/r/the-office-bar-and-grill-san-carlos', 'https://www.opentable.com/la-gare-french-restaurant', 'https://www.opentable.com/bisou-french-bistro', 'https://www.opentable.com/r/atwater-tavern-san-francisco', 'https://www.opentable.com/gaspar-brasserie', 'https://www.opentable.com/r/basilico-cucina-italiana-santa-rosa', 'https://www.opentable.com/salitos', 'https://www.opentable.com/il-posto-trattoria', 'https://www.opentable.com/original-us-restaurant-unione-sportiva', 'https://www.opentable.com/r/kaori-sushi-and-sake-bar-san-mateo', 'https://www.opentable.com/arya-global-cuisine-redwood-city', 'https://www.opentable.com/tambo-restaurant', 'https://www.opentable.com/comstock-saloon', 'https://www.opentable.com/chou-chou-bistro', 'https://www.opentable.com/blush-raw-kitchen', 'https://www.opentable.com/coi', 'https://www.opentable.com/osteria-divino', 'https://www.opentable.com/red-tavern', 'https://www.opentable.com/r/albona-ristorante-istriano-san-francisco', 'https://www.opentable.com/angelicas-fine-dining-bar-and-entertainment', 'https://www.opentable.com/the-third-eye-restaurant-and-bar', 'https://www.opentable.com/r/the-oxford-sunnyvale', 'https://www.opentable.com/r/grand-lake-kitchen-oakland', 'https://www.opentable.com/cassava', 'https://www.opentable.com/the-brixton', 'https://www.opentable.com/caffe-delucchi', 'https://www.opentable.com/urfa-bistro', 'https://www.opentable.com/aliotos', 'https://www.opentable.com/sanraku-metreon', 'https://www.opentable.com/thai-bangkok-cuisine', 'https://www.opentable.com/bobs-steak-and-chop-house-san-francisco', 'https://www.opentable.com/best-of-burma', 'https://www.opentable.com/aq-restaurant-and-bar', 'https://www.opentable.com/bissap-and-little-baobab', 'https://www.opentable.com/ernestos-italian-restaurant', 'https://www.opentable.com/napa-valley-bistro', 'https://www.opentable.com/bar-cesar', 'https://www.opentable.com/rustic-house-san-carlos', 'https://www.opentable.com/laurel-court-restaurant-and-bar-fairmont-san-francisco', 'https://www.opentable.com/sabrosa', 'https://www.opentable.com/cafe-claude-downtown', 'https://www.opentable.com/lily-kai-chinese-cuisine', 'https://www.opentable.com/le-soleil', 'https://www.opentable.com/r/himchuli-restaurant-pleasanton', 'https://www.opentable.com/cera-una-volta', 'https://www.opentable.com/maruya', 'https://www.opentable.com/amelie-san-francisco', 'https://www.opentable.com/r/royal-taj-india-cuisine-campbell', 'https://www.opentable.com/east-coast-alice', 'https://www.opentable.com/r/panino-giusto-cupertino', 'https://www.opentable.com/r/point-noyo-fort-bragg', 'https://www.opentable.com/vino-locale', 'https://www.opentable.com/cafe-tiramisu', 'https://www.opentable.com/caffe-sport-san-francisco', 'https://www.opentable.com/fiore', 'https://www.opentable.com/uva-trattoria-napa', 'https://www.opentable.com/cafe-europa-san-francisco', 'https://www.opentable.com/r/abesha-ethiopian-cuisine-oakland', 'https://www.opentable.com/calistoga-inn-restaurant-and-brewery', 'https://www.opentable.com/mount-everest-restaurant', 'https://www.opentable.com/1601-bar-and-kitchen', 'https://www.opentable.com/spencers-san-jose', 'https://www.opentable.com/ali-baba', 'https://www.opentable.com/chalet-ticino', 'https://www.opentable.com/olema-farm-house-point-reyes-seashore-lodge', 'https://www.opentable.com/angelino-restaurant', 'https://www.opentable.com/india-clay-oven-restaurant-and-bar-richmond-district', 'https://www.opentable.com/bibis-burger-bar', 'https://www.opentable.com/r/palooza-gastropub-and-wine-bar-kenwood', 'https://www.opentable.com/new-delhi-restaurant', 'https://www.opentable.com/houlihans-at-the-holiday-inn-san-francisco-airport', 'https://www.opentable.com/minas-brazilian-restaurant', 'https://www.opentable.com/sons-and-daughters', 'https://www.opentable.com/r/il-borgo-san-francisco', 'https://www.opentable.com/la-briciola', 'https://www.opentable.com/faz-oakland', 'https://www.opentable.com/trellis-restaurant', 'https://www.opentable.com/biscuits-and-blues', 'https://www.opentable.com/vicoletto', 'https://www.opentable.com/troya-mediterranean', 'https://www.opentable.com/jacks-oyster-bar-and-fish-house', 'https://www.opentable.com/fior-d-italia-san-francisco', 'https://www.opentable.com/trapeze-european-cuisine', 'https://www.opentable.com/rosie-mccanns-santana-row', 'https://www.opentable.com/dirty-habit', 'https://www.opentable.com/spin-a-yarn', 'https://www.opentable.com/the-grill-at-silverado-resort', 'https://www.opentable.com/pranzi-italian-bistro', 'https://www.opentable.com/chili-house', 'https://www.opentable.com/cafe-bastille', 'https://www.opentable.com/ca-momi-osteria', 'https://www.opentable.com/fusion-peruvian-grill', 'https://www.opentable.com/los-moles-emeryville', 'https://www.opentable.com/seoul-garden', 'https://www.opentable.com/bay-view-restaurant-inn-at-the-tides', 'https://www.opentable.com/canneti-roadhouse-italiana', 'https://www.opentable.com/camp-bbq', 'https://www.opentable.com/el-mansour', 'https://www.opentable.com/burritt-room-and-tavern-mystic-hotel', 'https://www.opentable.com/the-voya', 'https://www.opentable.com/brindisi', 'https://www.opentable.com/the-lighthouse-bar-and-grill-mill-valley', 'https://www.opentable.com/indian-oven-haight', 'https://www.opentable.com/santorini-restaurant', 'https://www.opentable.com/fume-bistro-and-bar', 'https://www.opentable.com/r/8-dragons-restaurant-healdsburg', 'https://www.opentable.com/r/akemi-berkeley', 'https://www.opentable.com/shido', 'https://www.opentable.com/chouquets', 'https://www.opentable.com/mitama-japanese-restaurant', 'https://www.opentable.com/r/mozaic-santa-cruz', 'https://www.opentable.com/bartlett-hall', 'https://www.opentable.com/tap-415', 'https://www.opentable.com/the-pear-southern-bistro', 'https://www.opentable.com/izakaya-roku', 'https://www.opentable.com/pucquio-oakland', 'https://www.opentable.com/firehouse-no-1-gastropub', 'https://www.opentable.com/copenhagen-restaurant', 'https://www.opentable.com/z-cafe-and-bar-san-francisco', 'https://www.opentable.com/sauce-belden', 'https://www.opentable.com/r/the-county-bench-kitchen-and-bar-santa-rosa', 'https://www.opentable.com/ziba-restaurant', 'https://www.opentable.com/71-saint-peter-restaurant', 'https://www.opentable.com/hs-lordships', 'https://www.opentable.com/katias-russian-tea-room-and-restaurant', 'https://www.opentable.com/r/the-boon-fly-cafe-napa', 'https://www.opentable.com/napkins', 'https://www.opentable.com/r/la-boheme-palo-alto', 'https://www.opentable.com/the-waterfront-restaurant-and-cafe', 'https://www.opentable.com/mivan-mediterranean-cuisine', 'https://www.opentable.com/agriculture-public-house-at-dawn-ranch', 'https://www.opentable.com/carneros-bistro-and-wine-bar', 'https://www.opentable.com/lolivier', 'https://www.opentable.com/ristorante-umbria', 'https://www.opentable.com/billy-berks', 'https://www.opentable.com/five', 'https://www.opentable.com/r/table-29-at-the-doubletree-american-canyon', 'https://www.opentable.com/guiso-latin-fusion', 'https://www.opentable.com/mateos-cocina-latina', 'https://www.opentable.com/r/main-street-kitchen-walnut-creek', 'https://www.opentable.com/r/adventure-in-food-and-wine-san-francisco', 'https://www.opentable.com/r/mathilde-bistro-san-francisco', 'https://www.opentable.com/wise-sons-jewish-delicatessen', 'https://www.opentable.com/plouf', 'https://www.opentable.com/r/maybecks-san-francisco', 'https://www.opentable.com/r/my-pot-hot-pot-san-francisco', 'https://www.opentable.com/mona-lisa', 'https://www.opentable.com/hogs-apothecary', 'https://www.opentable.com/r/dum-indian-soul-food-san-francisco', 'https://www.opentable.com/r/tratto-san-francisco', 'https://www.opentable.com/tarla-grill', 'https://www.opentable.com/the-grill-story', 'https://www.opentable.com/r/olla-cocina-san-jose', 'https://www.opentable.com/menara-moroccan-restaurant', 'https://www.opentable.com/aicha', 'https://www.opentable.com/sauce-gough', 'https://www.opentable.com/r/ulterior-santa-cruz', 'https://www.opentable.com/roccos-cafe', 'https://www.opentable.com/arabian-nights', 'https://www.opentable.com/skool', 'https://www.opentable.com/bui-bistro', 'https://www.opentable.com/woodfour-brewing', 'https://www.opentable.com/bissap-baobab-oakland', 'https://www.opentable.com/mandarin-roots', 'https://www.opentable.com/lulu', 'https://www.opentable.com/bask-san-francisco', 'https://www.opentable.com/peter-lowells', 'https://www.opentable.com/yuubi-japanese-restaurant', 'https://www.opentable.com/calistoga-kitchen', 'https://www.opentable.com/luce-intercontinental-san-francisco', 'https://www.opentable.com/capannina', 'https://www.opentable.com/okane', 'https://www.opentable.com/baltica', 'https://www.opentable.com/palio-dasti', 'https://www.opentable.com/baby-blues-bbq-sf', 'https://www.opentable.com/manos-nouveau', 'https://www.opentable.com/grill-at-the-st-regis', 'https://www.opentable.com/mosaic-restaurant-and-lounge-san-jose', 'https://www.opentable.com/kolbeh-restaurant', 'https://www.opentable.com/ideal-bar-and-grill', 'https://www.opentable.com/regalito-rosticeria', 'https://www.opentable.com/fattoria-e-mare', 'https://www.opentable.com/celias-mexican-restaurant-palo-alto', 'https://www.opentable.com/pera-restaurant-san-francisco', 'https://www.opentable.com/r/phlox-commons-san-francisco', 'https://www.opentable.com/losteria-del-forno', 'https://www.opentable.com/hyde-street-seafood-house-and-raw-bar', 'https://www.opentable.com/back-nine-grill-and-bar', 'https://www.opentable.com/thai-spice', 'https://www.opentable.com/olea-restaurant', 'https://www.opentable.com/r/rangecafe-bar-and-grill-san-rafael', 'https://www.opentable.com/bay223', 'https://www.opentable.com/b-and-v-whiskey-bar-and-grille', 'https://www.opentable.com/r/veraison-calistoga', 'https://www.opentable.com/la-mere-michelle', 'https://www.opentable.com/orchestria-palm-court', 'https://www.opentable.com/loft-bar-and-bistro', 'https://www.opentable.com/butterfly-the-embarcadero', 'https://www.opentable.com/blue-mermaid-argonaut-hotel', 'https://www.opentable.com/chocolate-the-restaurant', 'https://www.opentable.com/zina-lounge', 'https://www.opentable.com/borobudur', 'https://www.opentable.com/ferry-plaza-seafood', 'https://www.opentable.com/sushi-hunter', 'https://www.opentable.com/nicos-hideaway', 'https://www.opentable.com/r/la-casa-restaurant-sonoma', 'https://www.opentable.com/naked-fish', 'https://www.opentable.com/krua-thai-san-francisco', 'https://www.opentable.com/zabu-zabu', 'https://www.opentable.com/sahaara-mediterranean-tapas', 'https://www.opentable.com/belcampo', 'https://www.opentable.com/gitane', 'https://www.opentable.com/hotel-damici-ristorante', 'https://www.opentable.com/37-north-doubletree-by-hilton-burlingame', 'https://www.opentable.com/huxley', 'https://www.opentable.com/arte-ristorante', 'https://www.opentable.com/noir-lounge', 'https://www.opentable.com/r/the-forge-napa', 'https://www.opentable.com/bon-vivant-palo-alto', 'https://www.opentable.com/local-kitchen-and-wine-merchant', 'https://www.opentable.com/r/tamarind-hall-san-francisco', 'https://www.opentable.com/jannah', 'https://www.opentable.com/the-barrel-room-san-francisco', 'https://www.opentable.com/the-q-restaurant-and-bar-fka-barbersq', 'https://www.opentable.com/castagna-san-francisco', 'https://www.opentable.com/siena-the-meritage-resort', 'https://www.opentable.com/terrace-cafe-and-veranda-bar-best-western-el-rancho-inn', 'https://www.opentable.com/ovo-tavern', 'https://www.opentable.com/mission-street-oyster-bar-and-seafood-restaurant', 'https://www.opentable.com/r/the-corner-napa', 'https://www.opentable.com/eight-noodle-shop', 'https://www.opentable.com/verge-restaurant-los-gatos', 'https://www.opentable.com/lottavo-san-francisco', 'https://www.opentable.com/st-helena-bistro', 'https://www.opentable.com/level-iii', 'https://www.opentable.com/r/sushi-hon-san-francisco', 'https://www.opentable.com/taheris-mediterranean-restaurant', 'https://www.opentable.com/fenix', 'https://www.opentable.com/hard-water', 'https://www.opentable.com/namu-gaji', 'https://www.opentable.com/hatcho', 'https://www.opentable.com/panta-rei', 'https://www.opentable.com/oola', 'https://www.opentable.com/kanishkas-gastro-pub', 'https://www.opentable.com/the-water-street-grill', 'https://www.opentable.com/ti-piacera', 'https://www.opentable.com/curbside-cafe', 'https://www.opentable.com/r/basalt-napa', 'https://www.opentable.com/yamasho', 'https://www.opentable.com/r/zzan-korean-fusion-san-francisco', 'https://www.opentable.com/urbano-latino', 'https://www.opentable.com/colombini-italian-cafe-and-bistro-nob-hill-hotel', 'https://www.opentable.com/r/revelry-bistro-san-francisco', 'https://www.opentable.com/b44', 'https://www.opentable.com/acquolina', 'https://www.opentable.com/r/zingari-ristorante-and-jazz-bar-san-francisco', 'https://www.opentable.com/dirty-water-restaurant-and-bar', 'https://www.opentable.com/oneup-restaurant-and-lounge-at-grand-hyatt-san-francisco', 'https://www.opentable.com/r/protea-yountville', 'https://www.opentable.com/ambience-los-altos', 'https://www.opentable.com/hangar-steak', 'https://www.opentable.com/urban-tavern-sf', 'https://www.opentable.com/hillside-supper-club', 'https://www.opentable.com/gardenias', 'https://www.opentable.com/pescatore-san-francisco', 'https://www.opentable.com/magic-flute', 'https://www.opentable.com/the-liberties-bar-and-restaurant', 'https://www.opentable.com/mkt-restaurant-and-bar', 'https://www.opentable.com/mikaku-restaurant', 'https://www.opentable.com/kitchen-story', 'https://www.opentable.com/restaurant/profile/270820?p=2&sd=2017-02-12%2019%3A00', 'https://www.opentable.com/r/the-reel-fish-house-and-grill-sonoma', 'https://www.opentable.com/parallel-37', 'https://www.opentable.com/cesarios', 'https://www.opentable.com/brasserie-s-and-p', 'https://www.opentable.com/townie', 'https://www.opentable.com/caffe-fiore-san-francisco', 'https://www.opentable.com/trace', 'https://www.opentable.com/cease-and-desist', 'https://www.opentable.com/1313-main', 'https://www.opentable.com/aliment', 'https://www.opentable.com/r/hashiri-san-francisco', 'https://www.opentable.com/398-brasserie', 'https://www.opentable.com/r/oec-san-francisco', 'https://www.opentable.com/r/bota-tapas-and-paella-bar-san-francisco', 'https://www.opentable.com/anzu', 'https://www.opentable.com/aquitaine-san-francisco']
    print len(a)
    #ver = raw_input("rating:")
    ver = "4~5"
    startidx = raw_input("시작:")
    endidx = raw_input("끝:")
    with xlsxwriter.Workbook("SanFran("+ver+")"+startidx+"-"+endidx+".xlsx") as workbook2:
        startidx = int(startidx)
        endidx = int(endidx)
        print startidx, "~", endidx, "처리중"
        print a[startidx-1:endidx]
        get_infotest(a[startidx-1:endidx], workbook2)
        print startidx, "~",endidx,"처리완료"
    #"""
__main__()
#workbook.close()
