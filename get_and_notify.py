import boto3
import urllib3
from bs4 import BeautifulSoup
import os
import schedule
import time

s3 = boto3.resource("s3",
        aws_access_key_id=os.environ.get("AWS_KEY"),
        aws_secret_access_key=os.environ.get("AWS_TOKEN"),
        region_name="ap-northeast-1")
obj = s3.Object("hiu-notify","old.txt")
obj_data = obj.get()["Body"].read().decode("utf-8").replace("\r","")

def do():
    url = os.environ.get("notifyurl")
    http = urllib3.PoolManager()
    res = http.request("GET",url)
    res_html = BeautifulSoup(res.data,"html.parser").prettify()
    res_html = res_html[res_html.find("トピックス"):res_html.find("<!-- /#newsTopicsWrap -->")-5]
    
    tmp = res_html[res_html.find("https://"):]
    link = tmp[:tmp.find('"')]
    tmp = tmp[tmp.find("title")+8:]
    title = tmp[:tmp.find("<")-10]
    new = link+"\n"+title

    if obj_data != new:
        line_token = os.environ.get("LINE_TOKEN")
        line_url = "https://notify-api.line.me/api/notify"
        headers = {"Authorization": "Bearer " + line_token}
        fields = {"message": f"[ NEW INFORMATION ]\n{title}\n{link}"}
        http.request("POST",
                    line_url,
                    headers=headers,
                    fields=fields)
        obj.put(Body=new.encode("utf-8"),
                ContentEncoding="utf-8",
                ContentType="text/plane")

schedule.every(10).minutes.do(do)

while True:
    print("check...")
    schedule.run_pending()
    time.sleep(10)