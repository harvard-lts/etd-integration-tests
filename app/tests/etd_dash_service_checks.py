import time
import os
import json
from celery import Celery
import pysftp
import glob
import shutil
import requests


class ETDDashServiceChecks():

    def dash_deposit_test(self):
        result = {"num_failed": 0,
                  "tests_failed": [],
                  "info": {}}
        incoming_queue = os.environ.get('FIRST_QUEUE_NAME',
                                        'etd_submission_ready')

        # proquest2dash test vars
        private_key = os.getenv("PRIVATE_KEY_PATH")
        remoteSite = os.getenv("dropboxServer")
        remoteUser = os.getenv("dropboxUser")
        archiveDir = "archives/gsd"
        incomingDir = "incoming/gsd"
        zipFile = "submission_999999.zip"

        FEATURE_FLAGS = "feature_flags"
        DASH_FEATURE_FLAG = "dash_feature_flag"

        # Send a simple task (create and send in 1 step)
        # res = client.send_task('tasks.tasks.do_task',
        # args=[{"job_ticket_id":"123","hello":"world"}],
        # kwargs={}, queue=incoming_queue)
        # read from 'final_queue' to see that it went through the pipeline

        client = Celery('app')
        client.config_from_object('celeryconfig')

        messagefile = os.environ.get('MESSAGE_FILE', "message.json")
        with open(messagefile) as f:
            messagejson = f.read()
        message = json.loads(messagejson)

        # only prep test object if dash integration feature flag is on
        if FEATURE_FLAGS in message:
            feature_flags = message[FEATURE_FLAGS]
            # new_message[FEATURE_FLAGS] = feature_flags
            if (DASH_FEATURE_FLAG in feature_flags and
                    feature_flags[DASH_FEATURE_FLAG] == "on"):

                # clear out any old test object
                if glob.glob('/home/etdadm/data/in/proquest*-999999-gsd/submission_999999.zip'):  # noqa: E501
                    for filename in glob.glob('/home/etdadm/data/in/proquest*-999999-gsd/*'):  # noqa: E501
                        os.remove(filename)
                    for filename in glob.glob('/home/etdadm/data/in/proquest*-999999-gsd'):  # noqa: E501
                        shutil.rmtree(filename)

                # put the test object in the dropbox
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
                        sftp.put(f"./testdata/{zipFile}",
                                 f"{incomingDir}/{zipFile}")
                except Exception as err:
                    result["num_failed"] += 1
                    result["tests_failed"].append("SFTP")
                    result["info"] = {"Proquest Dropbox sftp failed":
                                      {"status_code": 500,
                                       "text": str(err)}}

                resp_text = self.check_for_duplicates()
                if resp_text != "[]":
                    uuid = json.loads(resp_text)[0]["uuid"]
                    url = f"{self.rest_url}/items/{uuid}"
                    session_key = self.get_session_key()
                    headers = {'Cookie': session_key}
                    response = requests.delete(url, headers=headers,
                                               verify=False)

                    if response.status_code != 200:
                        result["num_failed"] += 1
                        result["tests_failed"].append("DASH")
                        result["info"] = {"DASH delete failed":
                                          {"status_code": 500,
                                           "text": "Delete failed"}}

                '''
                try:
                    if self.check_for_duplicates():
                        result["num_failed"] += 1
                        result["tests_failed"].append("DASH")
                        result["info"] = {"Duplicate check failed":
                                          {"status_code": 500,
                                           "text": "Duplicate found"}}
                except Exception as err:
                    result["num_failed"] += 1
                    result["tests_failed"].append("DASH")
                    result["info"] = {"Duplicate check failed":
                                      {"status_code": 500,
                                       "text": str(err)}}
                try:
                    self.get_session_key()
                except Exception as err:
                    result["num_failed"] += 1
                    result["tests_failed"].append("DASH")
                    result["info"] = {"DASH login failed":
                                      {"status_code": 500,
                                       "text": str(err)}} '''

        client.send_task(name="etd-dash-service.tasks.send_to_dash",
                         args=[message], kwargs={}, queue=incoming_queue)

        sleep_secs = int(os.environ.get('SLEEP_SECS', 2))

        time.sleep(sleep_secs)  # wait for queue

        return result

    def check_for_duplicates(self):
        identifier = os.getenv("SUBMISSION_PQ_ID")
        rest_url = os.getenv("DASH_REST_URL",
                             "https://dash.harvard.edu/rest")
        query_url = f"{rest_url}/items/find-by-metadata-field"
        json_query = {"key": "dc.identifier.other", "value": identifier}
        resp = requests.post(query_url, json=json_query, verify=False)
        return resp.text
        '''if resp.text == "[]":
            return False
        else:
            return True'''

    def get_session_key(self):
        rest_url = os.getenv("DASH_REST_URL",
                             "https://dash.harvard.edu/rest")
        login_url = f"{rest_url}/login"
        login_email = os.getenv("DASH_LOGIN_EMAIL")
        login_pw = os.getenv("DASH_LOGIN_PW")
        login_info = f'email={login_email}&password={login_pw}'
        resp = requests.post(login_url, data=login_info, verify=False)
        return resp.cookies.get('JSESSIONID')
