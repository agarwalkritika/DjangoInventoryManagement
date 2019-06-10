import requests
import json

BASE_URL = "http://localhost:8000/api/"


def get_records():
    api = "inventory"
    url = BASE_URL + api
    res = requests.get(url=url)
    return res.json()


def create_record():
    api = "inventory"
    url = BASE_URL+api
    record = [{
        "product_id": "C2012",
        "product_name": "uqusamrht",
        "vendor": "FFFD",
        "mrp": 2000.4,
        "batch_num": "A1214",
        "batch_date": "1999-12-11",
        "quantity": 4,
        "status": "APPROVED"
    }]
    res = requests.put(url=url, data=json.dumps(record))
    print (res)
    print (res.text)


def approve(id):
    url = BASE_URL + "approvals"
    res = requests.post(url=url, data=json.dumps({"id":id}))
    print (res)
    print (res.text)

# all_records = get_records()
# print (all_records)
# create_record()
approve(5)
