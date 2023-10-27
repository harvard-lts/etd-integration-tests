import time
import os
import json
from celery import Celery
import pysftp
import glob
import shutil
import requests
import random
import string
import logging


class ETDDashServiceChecks():

    def __init__(self):
        self.logger = logging.getLogger('etd_int_tests')

    def dash_deposit_test(self):
        self.logger.info(">>> Starting integration test")
        result = {"num_failed": 0,
                  "tests_failed": [],
                  "info": {}}
        incoming_queue = os.environ.get('FIRST_QUEUE_NAME',
                                        'etd_submission_ready')

        FEATURE_FLAGS = "feature_flags"
        DASH_FEATURE_FLAG = "dash_feature_flag"

        client = Celery('app')
        client.config_from_object('celeryconfig')

        self.logger.info(">>> Read message file")
        messagefile = os.environ.get('MESSAGE_FILE', "message.json")
        with open(messagefile) as f:
            messagejson = f.read()
        message = json.loads(messagejson)

        # only prep test object if dash integration feature flag is on
        if FEATURE_FLAGS in message:
            feature_flags = message[FEATURE_FLAGS]
            if (DASH_FEATURE_FLAG in feature_flags and
                    feature_flags[DASH_FEATURE_FLAG] == "on"):

                base_name = self.random_digit_string()
                # 1. clear out any old test object
                self.logger.info(">>> Cleanup test object")
                self.cleanup_test_object(base_name)

                # 2. put the test object in the dropbox
                self.logger.info(">>> SFTP test object")
                try:
                    self.sftp_test_object(base_name)
                except Exception as err:
                    result["num_failed"] += 1
                    result["tests_failed"].append("SFTP")
                    result["info"] = {"Proquest Dropbox sftp failed":
                                      {"status_code": 500,
                                       "text": str(err)}}
                    self.logger.error(str(err))

                # 3. send the test object to dash
                self.logger.info(">>> Submit test object to dash")
                client.send_task(name="etd-dash-service.tasks.send_to_dash",
                                 args=[message], kwargs={},
                                 queue=incoming_queue)
                sleep_secs = int(os.environ.get('SLEEP_SECS', 30))
                time.sleep(sleep_secs)  # wait for queue

                rest_url = os.getenv("DASH_REST_URL")
                self.logger.info(">>> Check dash for test object")
                resp_text = self.get_dash_object()

                # 4. check that mapfile exists and contains the correct
                # handle
                # log resp_text for debugging
                self.logger.debug(">>> Dash object: " + resp_text)
                handle = json.loads(resp_text)[0]["handle"]
                sub_id = f"submission_{base_name}"
                # read mapfile in out/ directory
                out_dir = os.environ.get('ETD_OUT_DIR')
                mapfile_path = f'{out_dir}/proquest*-{base_name}-gsd/mapfile'
                if glob.glob(mapfile_path):
                    for filename in glob.glob(mapfile_path):
                        with open(filename) as f:
                            mapfile = f.read()
                            # make sure contents of mapfile are exactly
                            # sub_id + " " + handle
                            if mapfile != sub_id + " " + handle:
                                result["num_failed"] += 1
                                result["tests_failed"].append("MAPFILE_CONTENTS")  # noqa: E501
                                result["info"] = {"Mapfile contents incorrect":
                                                  {"status_code": 500,
                                                   "text": f"Mapfile: {mapfile_path}"}}  # noqa: E501
                                self.logger.error(f"Mapfile contents incorrect: {mapfile_path}")  # noqa: E501
                else:
                    # mapfile not found, record error result
                    result["num_failed"] += 1
                    result["tests_failed"].append("MAPFILE_NOT_FOUND")
                    result["info"] = {"Mapfile not found":
                                      {"status_code": 500,
                                       "text": f"Mapfile not found: {mapfile_path}"}}  # noqa: E501
                    self.logger.error(f"Mapfile not found: {mapfile_path}")
                
                # 5. count should be 1, shows insertion into dash
                count = len(json.loads(resp_text))
                if count != 1:
                    result["num_failed"] += 1
                    result["tests_failed"].append("DASH")
                    result["info"] = {"DASH count failed":
                                      {"status_code": 500,
                                       "url": rest_url,
                                       "count": count,
                                       "text": resp_text}}
                    self.logger.error("Count is not 1: " + resp_text)
                # 6. cleanup the test object from the filesystem
                self.logger.info(">>> Clean up test object")
                self.cleanup_test_object(base_name)

                # 7. put the test object in the dropbox for a second time
                # generate a random base name for the test object to make
                # duplicate detection more robust
                base_name = self.random_digit_string()
                dupe_dir = os.environ.get('ETD_DUPE_DIR')
                dupe_name_pattern = "proquest*-" + base_name + "-gsd_*"
                pre_dupe_count = len(glob.glob
                                     (f'{dupe_dir}/{dupe_name_pattern}'))

                try:
                    self.logger.info(">>> SFTP duplicate test object")
                    self.sftp_test_object(base_name)
                except Exception as err:
                    result["num_failed"] += 1
                    result["tests_failed"].append("SFTP")
                    result["info"] = {"Proquest Dropbox sftp failed":
                                      {"status_code": 500,
                                       "text": str(err)}}
                    self.logger.error(str(err))
                client.send_task(name="etd-dash-service.tasks.send_to_dash",
                                 args=[message], kwargs={},
                                 queue=incoming_queue)
                time.sleep(sleep_secs)  # wait for queue
                self.logger.info(">>> Check dash for duplicate test object")
                resp_text = self.get_dash_object()
                count = len(json.loads(resp_text))

                # 8. count shouldn't be 2, no duplicate insertion allowed
                if count == 2:
                    result["num_failed"] += 1
                    result["tests_failed"].append("DASH")
                    result["info"] = {"DASH count failed":
                                      {"status_code": 500,
                                       "url": rest_url,
                                       "count": count,
                                       "text": resp_text}}
                    self.logger.error("Count is 2: " + resp_text)

                # 9. check the dupe directory to make sure
                # the test object is there
                post_dupe_count = len(glob.glob
                                      (f'{dupe_dir}/{dupe_name_pattern}'))
                if post_dupe_count != pre_dupe_count + 1:
                    result["num_failed"] += 1
                    result["tests_failed"].append("DASH_DUPE")
                    result["info"] = {"DASH dupe directory failed":
                                      {"status_code": 500,
                                       "text": "Dupe directory not found:" +
                                       dupe_name_pattern + ". Expected: " +
                                       str(pre_dupe_count + 1) + " Found: " +
                                       str(post_dupe_count)}}

                # 10. delete the test object from dash
                self.logger.info(">>> Delete duplicate test object from dash")
                if resp_text != "[]":
                    uuid = json.loads(resp_text)[0]["uuid"]
                    url = f"{rest_url}/items/{uuid}"
                    session_key = self.get_session_key()
                    headers = {'Cookie': f'JSESSIONID={session_key}'}
                    response = requests.delete(url, headers=headers,
                                               verify=False)

                    if response.status_code != 200:
                        result["num_failed"] += 1
                        result["tests_failed"].append("DASH")
                        result["info"] = {"DASH delete failed":
                                          {"status_code": response.status_code,
                                           "url": url,
                                           "uuid": uuid,
                                           "session_key": session_key,
                                           "text": "Delete failed"}}
                        self.logger.error("Delete failed: " + response.text)

                # 11. cleanup the test object from the filesystem
                self.logger.info(">>> Clean up duplicate test object")
                self.cleanup_test_object(base_name)

            else:
                client.send_task(name="etd-dash-service.tasks.send_to_dash",
                                 args=[message], kwargs={},
                                 queue=incoming_queue)

                sleep_secs = int(os.environ.get('SLEEP_SECS', 2))

                time.sleep(sleep_secs)  # wait for queue

        return result

    def get_dash_object(self):
        rest_url = os.getenv("DASH_REST_URL",
                             "https://dspace6-qai.lib.harvard.edu/rest")
        identifier = os.getenv("SUBMISSION_PQ_ID")
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
                             "https://dspace6-qai.lib.harvard.edu/rest")
        login_url = f"{rest_url}/login"
        login_email = os.getenv("DASH_LOGIN_EMAIL")
        login_pw = os.getenv("DASH_LOGIN_PW")
        login_info = {"email": login_email, "password": login_pw}
        resp = requests.post(login_url, data=login_info, verify=False)
        return resp.cookies.get('JSESSIONID')

    def cleanup_test_object(self, base_name):
        if glob.glob('/home/etdadm/data/in/proquest*-' + base_name + '-gsd/submission_' + base_name + '.zip'):  # noqa: E501
            for filename in glob.glob('/home/etdadm/data/in/proquest*-' + base_name + '-gsd/*'):  # noqa: E501
                os.remove(filename)
            for filename in glob.glob('/home/etdadm/data/in/proquest*-' + base_name + '-gsd'):  # noqa: E501
                shutil.rmtree(filename)

    def sftp_test_object(self, base_name):
        # proquest2dash test vars
        private_key = os.getenv("PRIVATE_KEY_PATH")
        remoteSite = os.getenv("dropboxServer")
        remoteUser = os.getenv("dropboxUser")
        archiveDir = "archives/gsd"
        incomingDir = "incoming/gsd"
        zipFile = "submission_999999.zip"
        newZipFile = "submission_" + base_name + ".zip"
        with pysftp.Connection(host=remoteSite,
                               username=remoteUser,
                               private_key=private_key) as sftp:
            # remove any existing test object
            if sftp.exists(f"{archiveDir}/{zipFile}"):
                sftp.remove(f"{archiveDir}/{zipFile}")
            # sftp test object to incoming dir
            try:
                sftp.put(f"./testdata/{zipFile}",
                         f"{incomingDir}/{newZipFile}")
            except Exception as err:
                self.logger.error(f"SFTP error: {err}")

    # Method to return a random string of 10 digits
    def random_digit_string(self):
        return ''.join(random.choices(string.digits, k=10))
