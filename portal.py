import boto3
from bs4 import BeautifulSoup
import os
import schedule
import time
import difflib
import urllib3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

WAITTIME = 10

options = Options()
options.add_argument('--disable-gpu')
options.add_argument('--disable-extensions')
options.add_argument('--proxy-server="direct://"')
options.add_argument('--proxy-bypass-list=*')
options.add_argument('--start-maximized')
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
    webdrv = webdriver.Chrome()
    webdrv.get(url)
    webdrv.find_element_by_xpath("/html/body/div/div/main/div/div/a").click()
    time.sleep(WAITTIME)
    webdrv.find_element_by_xpath('//*[@id="username"]').send_keys("s2021140")
    webdrv.find_element_by_xpath('//*[@id="password"]').send_keys("Andromeda_77")
    webdrv.find_element_by_css_selector("#submit").click()
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
        line_url = "https://notify-api.line.me/api/notify"
        headers = {"Authorization": "Bearer " + line_token}
        msg = "[ HIU Portalが更新されました ]\n"
        for d in dlist:
            msg += d[1] + "\n" + d[0] + "\n\n"
        fields = {"message": msg}
        http.request("POST",
                    line_url,
                    headers=headers,
                    fields=fields)
        new = ""
        for i in range(len(links)):
            new += links[i] + "\n" + texts[i] + "\n"
        new = new[:-1]
        obj.put(Body=new.encode("utf-8"),
                ContentEncoding="utf-8",
                ContentType="text/plane")
    webdrv.quit()
    print("finished")

schedule.every(10).minutes.do(func)
func()

while True:
    #print("check...")
    schedule.run_pending()
    time.sleep(10)