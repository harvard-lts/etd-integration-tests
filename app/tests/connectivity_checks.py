import requests
import os
from pymongo import MongoClient

class ConnectivityChecks():

    def mongodb_connectivity_test(self):
        result = {"num_failed": 0,
                  "tests_failed": [], "info": {}}

        # read from mongodb
        mongo_url = os.environ.get('MONGO_URL')
        try:
            mongo_client = MongoClient(mongo_url, maxPoolSize=1)
            # mongo_db = mongo_client[mongo_dbname]
            mongo_client.close()

        except Exception as err:
            result = {"num_failed": 1,
                  "tests_failed": ["Mongo"], 
                  "info": {"Failed Mongo": {"status_code": 500, "text": str(err)}}}
            mongo_client.close()
        return result

    def dash_connectivity_test(self):
        result = {"num_failed": 0,
                  "tests_failed": [], "info": {}}
        # DASH healthcheck
        dash_url = os.environ.get('DASH_URL')
        try:
            dash_response = requests.get(dash_url, verify=False)
            if dash_response.status_code != 200:
                result = {"num_failed": 1,
                  "tests_failed": ["DASH"], 
                  "info": {"DASH HTTP error": {"status_code":
                                             dash_response.status_code}}}

        except Exception as err:
            result = {"num_failed": 1,
                  "tests_failed": ["DASH"], 
                  "info": {"DASH HTTP error": {"status_code": 500,
                                         "text": str(err)}}}
        return result

    def dims_connectivity_test(self):
        result = {"num_failed": 0,
                  "tests_failed": [], "info": {}}
        # DIMS healthcheck
        dims_url = os.environ.get('DIMS_URL') 
        try:
            dims_response = requests.get(dims_url, verify=False)
            if dims_response.status_code != 200:
                result = {"num_failed": 1,
                "tests_failed": ["DASH"], 
                  "info": {"DIMS HTTP error": {"status_code":
                                             dims_response.status_code}}}
        except Exception as err:
            result = {"num_failed": 1,
                  "tests_failed": ["DASH"], 
                  "info": {"DIMS HTTP error": {"status_code": 500,
                                         "text": str(err)}}}
        return result

