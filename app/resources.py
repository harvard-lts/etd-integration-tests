import re
import glob
import shutil
import time
import requests, traceback
from flask_restx import Resource, Api
from flask import render_template, current_app
import os, os.path, json
import certifi
import ssl
from pymongo import MongoClient
#from celery import Celery
from tasks.tasks import do_task, get_end_message
import random, boto3


incoming_queue = os.environ.get('FIRST_QUEUE_NAME', 'etd_submission_ready')
completed_ETDforum_queue = os.environ.get('LAST_QUEUE_NAME', 'etd_in_storage')


def define_resources(app):
    api = Api(app, version='1.0', title='ETD Integration Tests',
              description='This project contains the integration tests for the ETD project')
    dashboard = api.namespace('/', 
                              description="This project contains the integration tests for the ETD project")

    # Env vars
    mongo_url = os.environ.get('MONGO_URL')
    mongo_dbname = os.environ.get('MONGO_DBNAME')
    mongo_collection_name = os.environ.get('MONGO_COLLECTION')
    mongo_ssl_cert = os.environ.get('MONGO_SSL_CERT')
    sleep_secs = int(os.environ.get('SLEEP_SECS', 2))

    etd_access_key = os.environ.get('S3_ETD_ACCESS_KEY')
    etd_secret_key = os.environ.get('S3_ETD_SECRET_KEY')
    etd_bucket_name = os.environ.get('S3_ETD_BUCKET')
    etd_s3_endpoint = os.environ.get('S3_ETD_ENDPOINT')
    etd_s3_region = os.environ.get('S3_ETD_REGION')

    s3_test_prefix = os.environ.get('S3_TEST_PREFIX')

    dashboard_url = os.environ.get('DASHBOARD_URL')


    # Version / Heartbeat route
    @dashboard.route('/version', endpoint="version", methods=['GET'])
    class Version(Resource):
        def get(self):
            version = os.environ.get('APP_VERSION', "NOT FOUND")
            return {"version": version}


    @app.route('/integration')
    def integration_test():
        num_failed_tests = 0
        tests_failed = []
        result = {"num_failed": num_failed_tests, "tests_failed": tests_failed, "info": {}}

        # Send a simple task (create and send in 1 step)
        # res = client.send_task('tasks.tasks.do_task', args=[{"job_ticket_id":"123","hello":"world"}], kwargs={}, queue=incoming_queue)
        # read from 'final_queue' to see that it went through the pipeline
        job_ticket_id = str(random.randint(1, 4294967296))
        test_message = {"job_ticket_id":job_ticket_id, "integration_test": True}
        task_result = do_task(test_message)
        task_id = task_result.id
        # dump json
        current_app.logger.info("job ticket id: " + job_ticket_id)
        time.sleep(sleep_secs) # wait for queue 

        # read from mongodb
        try:
            mongo_client = MongoClient(mongo_url, maxPoolSize=1)
            mongo_db = mongo_client[mongo_dbname]
            mongo_client.close()

        except Exception as err:
            result["num_failed"] += 1
            result["tests_failed"].append("Mongo")
            result["Failed Mongo"] = {"status_code": 500, "text": str(err) }
            mongo_client.close()

        # Check S3 buckets
        try:
            etd_boto_session = boto3.Session(aws_access_key_id=etd_access_key, aws_secret_access_key=etd_secret_key)
            etd_s3_resource = etd_boto_session.resource('s3')
            etd_s3_bucket = etd_s3_resource.Bucket(etd_bucket_name)

            try:
                etd_s3_bucket.Object().last_modified
            except Exception as err:
                result["num_failed"] += 1
                result["tests_failed"].append("etd")
                result["Failed etd bucket"] = {"status_code": 500, "text": str(err) }
                traceback.print_exc()

            # todo- delete contents of s3 test thesis to reset test
            # etd_s3_bucket.objects.filter(Prefix=s3_test_prefix).delete()

        except Exception as err:
            result["num_failed"] += 1
            result["tests_failed"].append("S3")
            result["Failed S3"] = {"status_code": 500, "text": str(err) }

        # check if dashboard is running
        # leaving this test in for if/when etd has a dashboard
        # try:
        #     dashboard_response = requests.get(dashboard_url, verify=False)
        #     if dashboard_response.status_code != 200:
        #         result["num_failed"] += 1
        #         result["tests_failed"].append("Dashboard")
        #         result["Dashboard HTTP Error"] = {"status_code": dashboard_response.status_code}
        # except Exception as err:
        #     result["num_failed"] += 1
        #     result["tests_failed"].append("Dashboard")
        #     result["Dashboard HTTP Error"] = {"status_code": 500, "text": str(err) }

        return json.dumps(result)



    

