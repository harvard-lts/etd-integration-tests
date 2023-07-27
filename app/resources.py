import time
import requests
from flask_restx import Resource, Api
import os
import os.path
import json
from pymongo import MongoClient
# from tasks.tasks import start_test
from celery import Celery
import pysftp


incoming_queue = os.environ.get('FIRST_QUEUE_NAME', 'etd_submission_ready')
completed_queue = os.environ.get('LAST_QUEUE_NAME', 'etd_in_storage')


def define_resources(app):
    api = Api(app, version='1.0', title='ETD Integration Tests',
              description='This project contains the integration' +
                          'tests for the ETD project')
    dashboard = api.namespace('/',
                              description="This project contains " +
                              "the integration tests for " +
                              "the ETD project")

    # Env vars
    mongo_url = os.environ.get('MONGO_URL')
    # mongo_dbname = os.environ.get('MONGO_DBNAME')
    # mongo_collection_name = os.environ.get('MONGO_COLLECTION')
    # mongo_ssl_cert = os.environ.get('MONGO_SSL_CERT')
    sleep_secs = int(os.environ.get('SLEEP_SECS', 2))

#   dashboard_url = os.environ.get('DASHBOARD_URL')
    dash_url = os.environ.get('DASH_URL')
    dims_url = os.environ.get('DIMS_URL')

    # proquest2dash test vars
    private_key = os.getenv("PRIVATE_KEY_PATH")
    remoteSite = os.getenv("dropboxServer")
    remoteUser = os.getenv("dropboxUser")
    archiveDir = "archives/gsd"
    incomingDir = "incoming/gsd"
    zipFile = "submission_999999.zip"

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
        result = {"num_failed": num_failed_tests,
                  "tests_failed": tests_failed, "info": {}}

        # Send a simple task (create and send in 1 step)
        # res = client.send_task('tasks.tasks.do_task',
        # args=[{"job_ticket_id":"123","hello":"world"}],
        # kwargs={}, queue=incoming_queue)
        # read from 'final_queue' to see that it went through the pipeline
        messagefile = os.environ.get('MESSAGE_FILE', "message.json")
        with open(messagefile) as f:
            messagejson = f.read()
        message = json.loads(messagejson)
        client = Celery('app')
        client.config_from_object('celeryconfig')

        try:
            # cnopts = pysftp.CnOpts()
            # cnopts.hostkeys = known_hosts
            # cnopts = pysftp.CnOpts()
            # cnopts.hostkeys = None
            with pysftp.Connection(host=remoteSite,
                                   username=remoteUser,
                                   private_key=private_key) as sftp:
                if sftp.exists(f"{archiveDir}/{zipFile}"):
                    sftp.remove(f"{archiveDir}/{zipFile}")
                sftp.put(f"./data/{zipFile}",
                         f"{incomingDir}/{zipFile}")
        except Exception as err:
            result["num_failed"] += 1
            result["tests_failed"].append("SFTP")
            result["Proquest Dropbox sftp failed"] = {"status_code": 500,
                                                      "text": str(err)}

        client.send_task(name="etd-dash-service.tasks.send_to_dash",
                         args=[message], kwargs={}, queue=incoming_queue)

        time.sleep(sleep_secs)  # wait for queue

        # read from mongodb
        try:
            mongo_client = MongoClient(mongo_url, maxPoolSize=1)
            # mongo_db = mongo_client[mongo_dbname]
            mongo_client.close()

        except Exception as err:
            result["num_failed"] += 1
            result["tests_failed"].append("Mongo")
            result["Failed Mongo"] = {"status_code": 500, "text": str(err)}
            mongo_client.close()

        # DASH healthcheck
        try:
            dash_response = requests.get(dash_url, verify=False)
            if dash_response.status_code != 200:
                result["num_failed"] += 1
                result["tests_failed"].append("DASH")
                result["DASH HTTP error"] = {"status_code":
                                             dash_response.status_code}
        except Exception as err:
            result["num_failed"] += 1
            result["tests_failed"].append("DASH")
            result["DASH HTTP error"] = {"status_code": 500,
                                         "text": str(err)}

        # DIMS healthcheck
        try:
            dims_response = requests.get(dims_url, verify=False)
            if dims_response.status_code != 200:
                result["num_failed"] += 1
                result["tests_failed"].append("DIMS")
                result["DIMS HTTP Error"] = {"status_code":
                                             dims_response.status_code}
        except Exception as err:
            result["num_failed"] += 1
            result["tests_failed"].append("DIMS")
            result["DIMS HTTP Error"] = {"status_code": 500,
                                         "text": str(err)}

        # check if dashboard is running
        # leaving this test in for if/when etd has a dashboard
        # try:
        #     dashboard_response = requests.get(dashboard_url, verify=False)
        #     if dashboard_response.status_code != 200:
        #         result["num_failed"] += 1
        #         result["tests_failed"].append("Dashboard")
        #         result["Dashboard HTTP Error"] = {"status_code":
        #                               dashboard_response.status_code}
        # except Exception as err:
        #     result["num_failed"] += 1
        #     result["tests_failed"].append("Dashboard")
        #     result["Dashboard HTTP Error"] = {"status_code": 500,
        #                                       "text": str(err) }

        return json.dumps(result)
