# 公車資訊系統

---
## Introduction：
本系統為網頁網站，主要功能訴求在於：
1. 分析統整公車行駛數據，建立分析後資料。
2. 生產各項報表，利於使用者管理公車行駛行為等。
3. 以多種方式呈現視覺話數據，利於使用者觀察、比較各項統計結果。

## Environment：
**python3.8** with **Django2.2.24** <br>
work with **mySQL** & **MongoDB**

## Description：
基於作為縣市公車管理的輔助系統，本系統設計最初的主旨在於產生各項不同的報表，方便業者能夠基於公車的行駛紀錄自動產生相對應的電子化報表。
能夠有效地減少人工的時間與複雜度。
<br>
在此基礎之上，本系統亦陸續增加不同的數據分析的比較頁面、自動化運算結果的通知、資訊地理視覺畫的功能等，作為技術展示。

----

## Features:
### 1. 每日自動運算：
* 本站首頁呈現每日自動計算的結果。
* 在每天固定的時間(03:30)，程式將自動演算，遍歷前一天所有的公車紀錄，作為資料的前處理。
* 首頁呈現的資訊即是每日計算的結果。若有異常將會以紅色顯示
![Demo](demo/dashboard_demo.png)
* 
### 2. 報表：
* 可以條列式呈現各報表的名稱及功能，並且在選擇後羅列出產生報表所需的參數，供使勇者做選擇。
* 本站報表以python開發，設計特色在於能夠快速繼承基本樣板。除了既有的報表種類，亦能根據需求快速生成不同的報表。
* 除了以網頁瀏覽，報表也支援轉存pdf。
![Demo](demo/report_demo.png)

### 3. 站到站統計：
* 用以統計一個路線中，個站之間的行駛時間與等待時間時間的統計結果。
* 統計的方式能夠選擇平日、假日等日種類的選項，也能夠單獨以表格呈現一個站在24小時的統計變化。
* 為了直覺地顯示，這邊也提供了視覺畫的圖表供使用者參考。
![Demo](demo/stoptostop_demo.png)
### 4. 資料表比較：
* 此功能用來比較在不同條件下產生的報表數據差異性。
* 在此可以玄則比較的報表種類，填入相關參數後，系統將報表以左右對應的方式產生在畫面上。
![Demo](demo/compare_demo.png)
### ５. 數據地理資訊(地圖)：
* 導入真實地圖，將公車的行駛統計數據，以圖像的方時直覺呈現在地圖上。
* 導入時間段，可以動畫的方式觀看不同時間段在地圖上的數據變化。
![Demo](demo/map_demo.png)
### 6. 通知推播名單：
* 可以用來管理接收推播者的名單
* 整合LINE Notify，系統將自動推送每日計算結果到名單上的人。
* 使用者需要自行申請LINE Notify token，並依照LINE官方說明使用。
![Demo](demo/notify_demo.png)
### 6. 原始資料調用：
* 在做統計時，有時議會需要調閱原始資料。此頁面能夠調用公車車機回傳的原始資料，以及系統在做資料前處理後的結果。
![Demo](demo/rawdata_demo.png)

### 7.資料流量統計：
* 用圖表的方式呈現一天內，每個小時的資訊流量、事件回報量、公車在線處量、公車在路上的數量。
![Demo](demo/data_traffic_demo.png)
### 8. Swagger (API)：
* 作為網站的應用，本站亦提供許多彈性的api，作為整合的應用。
* 本站以Swagger UI來提供標準的說明與測試頁面，方便開發人員以清楚直覺的方式了解多項複雜的API應用格式。
![Demo](demo/swagger_demo.png)
### 9. Administration：
* 系統管理者頁面，此頁面提供了系統背景工作的詳細現狀與紀錄，以及其他各項資料庫操作選項，使資訊管理者能夠直接對原始資料做修改。
* 包括使用者的新增刪除、通知推播的新增刪除等；每日自動工作亦可在此調整。
![Demo](demo/admin_demo.png)
### Extra: 
* 本系統在使用者認證上有以OAuth串接Askey計有認證系統。
* 與一般Oauth部分相異，請參考下圖：
* **記得在user中新增使用者"oAuth"**
![Demo](demo/oauth_diagram.jpg)


----
## Installation：
### what you will need:
1. 欲建立此系統，需注意幾件事情：
   1. 此系統需配合
      1. Askey 既有公車系統的mysql & mongoDB 
      2. 使Django framework自由調用的mysql 
      3. 建立專門給此專案的.env file 內所需參數
   2. .env file 內所需參數
``` python
PROJECT_TITLE = <專案名稱>  # 可自由取名，名稱講呈現在網頁的sidebar上

DEBUG=False 
DJANGO_LOG_LEVEL = DEBUG 
SECRET_KEY= <Django secret key> 
# Django 相關參數，不贅述。

SERVER = xxx.xxx.xxx.xxx  # 請使用部署到的web ip(不可使用"*"，因為會使認證轉跳失敗)
SERVER_PORT = x  # 部署到的web port

TEMP_USER = oAuth
TEMP_PW = AskeyoAuth
# 作為oAuth預設登入的帳號密碼

EBUS_MONGODB = {"host":"xxx.xxx.xxx.xxx","port":x,"user":"<username>","password":"<password>"} 
# 填入雅敘用以記錄車輛drivelog的mongoDB相關資訊

EBUS_SQLDB = {"host":"xxx.xxx.xxx.xxx,"port":x,"user":"<username>","password":"<password>"} 
# 填入雅敘用以記錄中心資訊的mysql相關資訊

SITESQL_SCHEMA = <DB name>
SITESQL_HOST = xxx.xxx.xxx.xxx
SITESQL_PORT = x 
SITESQL_USER = <username> 
SITESQL_PW = <password>
# 作為Django framework調用的mysql相關資訊

TIME_SHIFT = 02  
# 日期分割的偏移量。預設以半夜12點作為日期的分割。但考慮到有行駛跨日的車輛，可設置時間偏移。
# 此例為02:00前發車的公車紀錄，屬於前一日的班次。

LINE_TOKEN = sy9uCRiHNBDVzCCvrDDKkUQtsroL4FD6YLym9XQAOaK 
TIME_ZONE = Asia/Taipei
```
### Installation Steps:
#### Step 1:
   * 將原始碼clone至專案資料夾

#### Step 2 :
   * 於專案資料集中新增.env
```$ touch .env```

#### Step 3 :
   * 將Django與資料庫 migrate
   * 以下兩行指令，將會自動與上步驟設定的資料庫migrate。Django 將自動在database中建立運作所需的table。
```
$ python manage.py makemigrations
$ python manage.py migrate
```
#### Step 4 :
* 建立super user
* 執行以下指令，跟著步驟建立superuser
```
$ python manage.py createsuperuser 
```

#### Step 5 : 
* 確認dockerfile中expose port與目前使用中的port沒有衝突
* Django webserver 預設使用port 8000作為介面，若有疑慮請更改dockerfile中的 CMD

#### Step 6 : 
* 執行docker build 以建立image
```
$ docker build --tag reportsite:mysite .
```
#### Step 7 : 
* 執行docker run 啟動container
* 請確認環境docker所使用的port
```
$ docker run -p {port}:{port} --log-opt max-size=10m --log-opt max-file=5 --name reportsite reportsite:mysite
```

#### Step 8 :
* Administration Page: http://{serverip}:{serverport}/admin/
* 以superuser帳號登入網頁Administration頁面，並新增user。
* 此user請按照.env中的 TEMP_USER & TEMP_PW 去建立。

----