import boto3
from bs4 import BeautifulSoup
import os
import schedule
import time
#import difflib
import urllib3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import requests
import json

WAITTIME = 10
LOCATION = '/app/.apt/usr/bin/google-chrome'
#LOCATION = "C:\Program Files (x86)\Google\Chrome\Application"

options = Options()
options.binary_location = LOCATION
options.add_argument('--disable-gpu')
options.add_argument('--disable-extensions')
#options.add_argument('--proxy-server="direct://"')
#options.add_argument('--proxy-bypass-list=*')
#options.add_argument('--start-maximized')
options.add_argument('--headless')

s3 = boto3.resource("s3",
        aws_access_key_id=os.environ.get("AWS_KEY"),
        aws_secret_access_key=os.environ.get("AWS_TOKEN"),
        region_name="ap-northeast-1")
obj = s3.Object("hiu-notify","old.txt")
obj_data = obj.get()["Body"].read().decode("utf-8").split("\n")
old_links = []
old_texts = []
for i in range(len(obj_data)//2):
    old_links.append(obj_data[2*i])
    old_texts.append(obj_data[2*i+1])

def func():
    print("triggered")
    http = urllib3.PoolManager()
    url = os.environ.get("portalurl")
    webdrv = webdriver.Chrome(chrome_options=options)
    webdrv.get(url)
    time.sleep(WAITTIME)
    print(webdrv.page_source)
    webdrv.find_element_by_css_selector("body > div > div > main > div > div > a:nth-child(6)").click()
    print("select login method")
    time.sleep(WAITTIME)
    webdrv.find_element_by_css_selector('#identifierId').send_keys(os.environ.get("loginid\n"))
    print("input id")
    time.sleep(WAITTIME)
    webdrv.find_element_by_css_selector('#password > div.aCsJod.oJeWuf > div > div.Xb9hP > input').send_keys(os.environ.get("loginpass\n"))
    print("input pass")
    time.sleep(WAITTIME)
    html = webdrv.page_source
    html = html[html.find("<tbody>"):html.find("</tbody>")+8]
    soup = BeautifulSoup(html,"html.parser")
    links = [a.get("href") for a in soup.find_all("a")]
    texts = [a.get_text()[45:-41] for a in soup.find_all("a")]
    dlist = []
    for i,l in enumerate(links):
        if not (l in old_links):
            dlist.append((l,texts[i]))

    #new_ = ""
    #for i in range(len(links)):
    #    new_ += links[i] + "\n" + texts[i] + "\n"
    #new_ = new_[:-1]
    #with open("old.txt","w",encoding="utf-8") as f:
    #    f.write(new_)

    if dlist:
        line_token = os.environ.get("LINE_TOKEN")
        line_url = "https://api.line.me/v2/bot/message/broadcast"
        line_header = {"Authorization": "Bearer " + line_token}
        msg = "[ HIU Portalが更新されました ]\n"
        for d in dlist:
            msg += d[1] + "\n" + d[0] + "\n\n"
        fields = {"messages": msg}
        http.request("POST",
                    line_url,
                    headers=line_header,
                    fields=fields)
        dtm_url = os.environ.get("DTMST_URL")
        msg_dtm = ""
        for d in dlist:
            msg_dtm += f"<{d[0]}|{d[1]}>\n"
        fields_dtm = {"text": msg_dtm}
        res_dtm = requests.post(dtm_url,data=json.dumps(fields_dtm))

        new = ""
        for i in range(len(links)):
            new += links[i] + "\n" + texts[i] + "\n"
        new = new[:-1]
        obj.put(Body=new.encode("utf-8"),
                ContentEncoding="utf-8",
                ContentType="text/plane")
    webdrv.quit()
    print("finished")

schedule.every().minute.at(":01").do(func)
schedule.every().minute.at(":31").do(func)
func()

while True:
    if (time.gmtime()[3] < 22-9) or (21 < time.gmtime()[3]):
        schedule.run_pending()
    time.sleep(10)