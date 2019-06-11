import requests
import json
import string
import random

# GLOBALS
BASE_URL = "http://localhost:8000/api/"

credentials = {
    "admin" : {
        "username" : "useradmin",
        "password" : "password"
    },
    "non-admin" : {
        "username" : "usernormal",
        "password" : "password"
    }
}


def get_random_string(length):
    final_string = ""
    for _ in range(length):
        final_string = final_string + random.choice(string.ascii_lowercase)
    return final_string

class TestFunctional:
    def test_1_get_auth_token(self, user="admin"):
        global headers
        url = BASE_URL + "login"
        data = credentials[user]
        print("Querying URL for login"+url)
        res = requests.post(url=url, data=json.dumps(data))
        print(res)
        if res.status_code != requests.codes.ok:
            assert False, "incorrect response"
        res_json = res.json()
        print(res_json)
        if 'x-inv-auth-token' in res_json and res_json['x-inv-auth-token']:
            print ("PASSED : Auth token successully obtained")
        else:
            assert False, "Auth token not recieved"
        self.headers = res_json

    def test_2_get_inventory_details(self):
        print("Getting Records")
        url = BASE_URL + "inventory"
        res = requests.get(url=url, headers=self.headers)
        if res.status_code == requests.codes.ok:
            assert True
        else:
            assert False

    def test_3_create_inventory_record(self):
        print("Creating Record")
        url = BASE_URL + "inventory"
        self.record = [{
            "product_id": get_random_string(5),
            "product_name": get_random_string(9),
            "vendor": get_random_string(4),
            "mrp": 2000.4,
            "batch_num": get_random_string(5),
            "batch_date": "1999-12-11",
            "quantity": 4,
            "status": "APPROVED"
        }]
        res = requests.put(url=url, data=json.dumps(self.record), headers=self.headers)
        print(res)
        print(res.text)
        assert res.status_code == requests.codes.ok

    def test_4_modify_inventory_record(self):
        print("Modify Record")
        url = BASE_URL + "inventory"
        self.record[0]['product_name'] = get_random_string(9)
        res = requests.post(url=url, data=json.dumps(self.record), headers=self.headers)
        print(res)
        print(res.text)
        assert res.status_code == requests.codes.ok

    def test_5_delete_record(self):
        print("Delete record")
        url = BASE_URL + "inventory"
        res = requests.delete(url=url, data=json.dumps(self.record), headers=self.headers)
        print(res)
        print(res.text)
        assert res.status_code == requests.codes.ok

    def test_6_get_all_approvals(self):
        url = BASE_URL + "approvals"
        res = requests.get(url=url, headers=self.headers)
        assert res.status_code == requests.codes.ok
        self.all_approvals = res.json()
        print(self.all_approvals)

    def test_7_approve_all_approvals(self):
        url = BASE_URL + "approvals"
        for approval in self.all_approvals:
            approval_id = approval['pk']
            try:
                res = requests.post(url=url, headers=self.headers, data=json.dumps({'id' : approval_id}))
                print(res)
                print(res.text)
                assert res.status_code == requests.codes.ok
            except AssertionError:
                print("Could not approve request #{}. Body was {}".format(approval_id, approval))


T = TestFunctional()
T.test_1_get_auth_token(user="admin")
T.test_2_get_inventory_details()
T.test_3_create_inventory_record()
T.test_4_modify_inventory_record()
T.test_5_delete_record()
T.test_6_get_all_approvals()
T.test_7_approve_all_approvals()

T1 = TestFunctional()
T1.test_1_get_auth_token(user="non-admin")
T1.test_2_get_inventory_details()
T1.test_3_create_inventory_record()
T.test_6_get_all_approvals()
T.test_7_approve_all_approvals()
T1.test_4_modify_inventory_record()
T.test_6_get_all_approvals()
T.test_7_approve_all_approvals()
T1.test_3_create_inventory_record()
T.test_6_get_all_approvals()
T.test_7_approve_all_approvals()
T1.test_5_delete_record()
T.test_6_get_all_approvals()
T.test_7_approve_all_approvals()
