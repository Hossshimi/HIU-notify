import boto3
import urllib3
from bs4 import BeautifulSoup
import os
import schedule
import time
import difflib
import re
#import selenium

s3 = boto3.resource("s3",
        aws_access_key_id=os.environ.get("AWS_KEY"),
        aws_secret_access_key=os.environ.get("AWS_TOKEN"),
        region_name="ap-northeast-1")
obj = s3.Object("hiu-notify","old.txt")
obj_data = obj.get()["Body"].read().decode("utf-8").split("\n")
#obj_data = "\n".join(obj_data)

def func():
    print("triggered")
    url = os.environ.get("notifyurl")
    http = urllib3.PoolManager()
    res = http.request("GET",url)
    res_html = BeautifulSoup(res.data,"html.parser").prettify().split("\n")[37:]
    #res_html = "\n".join(res_html)
    differ = difflib.Differ()
    diff = differ.compare(obj_data,res_html)
    dlist = []
    for d in diff:
        if d.startswith("+ "):
            dlist.append(d[2:].replace(" ",""))
    del dlist[0]
    with open("res.txt","w",encoding="utf-8") as f:
        f.write("\n".join(dlist))
    if dlist:
        line_token = os.environ.get("LINE_TOKEN")
        line_url = "https://notify-api.line.me/api/notify"
        headers = {"Authorization": "Bearer " + line_token}
        fields = {"message": f"[ NEW INFORMATION ]"}
        http.request("POST",
                    line_url,
                    headers=headers,
                    fields=fields)
        obj.put(Body="\n".join(res_html).encode("utf-8"),
                ContentEncoding="utf-8",
                ContentType="text/plane")
    print("finished")

schedule.every(10).minutes.do(func)
func()

while True:
    #print("check...")
    schedule.run_pending()
    time.sleep(10)