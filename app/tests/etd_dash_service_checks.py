import time
import os
import json
from celery import Celery
import pysftp
import glob
import shutil
import requests
import logging
from logging.handlers import TimedRotatingFileHandler

LOG_FILE_BACKUP_COUNT = 1
LOG_ROTATION = "midnight"
log_level = os.getenv("LOG_LEVEL", "DEBUG")
log_dir = os.getenv("LOG_DIR", "/home/etdadm/logs")
log_file_path = os.path.join(log_dir, "int_tests.log")
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = TimedRotatingFileHandler(
    filename=log_file_path,
    when=LOG_ROTATION,
    backupCount=LOG_FILE_BACKUP_COUNT
)
logger = logging.getLogger()
logger.addHandler(file_handler)
file_handler.setFormatter(formatter)
logger.setLevel(log_level)


class ETDDashServiceChecks():

    def dash_deposit_test(self):
        logger.info(">>> Starting integration test")
        result = {"num_failed": 0,
                  "tests_failed": [],
                  "info": {}}
        incoming_queue = os.environ.get('FIRST_QUEUE_NAME',
                                        'etd_submission_ready')

        FEATURE_FLAGS = "feature_flags"
        DASH_FEATURE_FLAG = "dash_feature_flag"

        client = Celery('app')
        client.config_from_object('celeryconfig')

        logger.info(">>> Read message file")
        messagefile = os.environ.get('MESSAGE_FILE', "message.json")
        with open(messagefile) as f:
            messagejson = f.read()
        message = json.loads(messagejson)

        # only prep test object if dash integration feature flag is on
        if FEATURE_FLAGS in message:
            feature_flags = message[FEATURE_FLAGS]
            if (DASH_FEATURE_FLAG in feature_flags and
                    feature_flags[DASH_FEATURE_FLAG] == "on"):

                # 1. clear out any old test object
                logger.info(">>> Cleanup test object")
                self.cleanup_test_object()

                # 2. put the test object in the dropbox
                logger.info(">>> SFTP test object")
                try:
                    self.sftp_test_object("999999")
                except Exception as err:
                    result["num_failed"] += 1
                    result["tests_failed"].append("SFTP")
                    result["info"] = {"Proquest Dropbox sftp failed":
                                      {"status_code": 500,
                                       "text": str(err)}}
                    logger.error(str(err))

                # 3. send the test object to dash
                logger.info(">>> Submit test object to dash")
                client.send_task(name="etd-dash-service.tasks.send_to_dash",
                                 args=[message], kwargs={},
                                 queue=incoming_queue)
                sleep_secs = int(os.environ.get('SLEEP_SECS', 30))
                time.sleep(sleep_secs)  # wait for queue

                rest_url = os.getenv("DASH_REST_URL")
                logger.info(">>> Check dash for test object")
                resp_text = self.get_dash_object()
                # 4. count should be 1, shows insertion into dash
                count = len(json.loads(resp_text))
                if count != 1:
                    result["num_failed"] += 1
                    result["tests_failed"].append("DASH")
                    result["info"] = {"DASH count failed":
                                      {"status_code": 500,
                                       "url": rest_url,
                                       "count": count,
                                       "text": resp_text}}
                    logger.error("Count is not 1: " + resp_text)
                # 5. cleanup the test object from the filesystem
                logger.info(">>> Clean up test object")
                self.cleanup_test_object()
                # 6. put the test object in the dropbox for a second time
                try:
                    logger.info(">>> SFTP duplicate test object")
                    self.sftp_test_object("999999")
                except Exception as err:
                    result["num_failed"] += 1
                    result["tests_failed"].append("SFTP")
                    result["info"] = {"Proquest Dropbox sftp failed":
                                      {"status_code": 500,
                                       "text": str(err)}}
                    logger.error(str(err))
                client.send_task(name="etd-dash-service.tasks.send_to_dash",
                                 args=[message], kwargs={},
                                 queue=incoming_queue)
                time.sleep(sleep_secs)  # wait for queue
                logger.info(">>> Check dash for duplicate test object")
                resp_text = self.get_dash_object()
                count = len(json.loads(resp_text))
                # 7. count shouldn't be 2, no duplicate insertion allowed
                if count == 2:
                    result["num_failed"] += 1
                    result["tests_failed"].append("DASH")
                    result["info"] = {"DASH count failed":
                                      {"status_code": 500,
                                       "url": rest_url,
                                       "count": count,
                                       "text": resp_text}}
                    logger.error("Count is 2: " + resp_text)

                # 8. delete the test object from dash
                logger.info(">>> Delete duplicate test object from dash")
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
                        logger.error("Delete failed: " + response.text)
                # 8. cleanup the test object from the filesystem
                logger.info(">>> Clean up duplicate test object")
                self.cleanup_test_object()

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

    def cleanup_test_object(self):
        if glob.glob('/home/etdadm/data/in/proquest*-999999-gsd/submission_999999.zip'):  # noqa: E501
            for filename in glob.glob('/home/etdadm/data/in/proquest*-999999-gsd/*'):  # noqa: E501
                os.remove(filename)
            for filename in glob.glob('/home/etdadm/data/in/proquest*-999999-gsd'):  # noqa: E501
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
            if sftp.exists(f"{archiveDir}/{zipFile}"):
                sftp.remove(f"{archiveDir}/{zipFile}")
                sftp.put(f"./testdata/{zipFile}",
                         f"{incomingDir}/{newZipFile}")
