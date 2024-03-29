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
import xml.etree.ElementTree as ET
import zipfile


class ETDEndToEnd():

    def __init__(self):
        self.logger = logging.getLogger('etd_int_tests')

    def end_to_end(self, indash=True):
        """
            Executes the end-to-end integration test.

            Args:
                indash (bool, optional): Flag indicating whether to
                this is an indash test.
                    Defaults to True.

            Returns:
                dict: A dictionary containing the test result with the
                following keys:
                    - num_failed (int): The number of failed tests.
                    - tests_failed (list): A list of failed test names.
                    - info (dict): Additional information about the
                    test result.
        """
        self.logger.info(">>> Starting integration test")
        result = {"num_failed": 0,
                  "tests_failed": [],
                  "info": {}}
        incoming_queue = os.environ.get('FIRST_QUEUE_NAME',
                                        'etd_submission_ready')

        client = Celery('app')
        client.config_from_object('celeryconfig')

        base_name = self.random_digit_string()

        # If the test object is for indash, use this one
        zipFile = "submission_999999.zip"
        schoolcode = "gsd"
        # Otherwise use the non-dash one
        if not indash:
            zipFile = "submission_no_dash.zip"
            schoolcode = "college"
        newZipFile = "submission_" + base_name + ".zip"
        shutil.copyfile(f"./testdata/{zipFile}", f"./testdata/{newZipFile}")

        self.replace_pq_id(base_name, f"./testdata/{newZipFile}")
        # put the test object in the dropbox
        self.logger.info(">>> SFTP test object")
        try:
            self.sftp_test_object(newZipFile, schoolcode)
        except Exception as err:
            result["num_failed"] += 1
            result["tests_failed"].append("SFTP")
            result["info"] = {"Proquest Dropbox sftp failed":
                              {"status_code": 500,
                               "text": str(err)}}
            self.logger.error(str(err))

        # # send the test object to dash
        self.logger.info(">>> Submit test object to dash")
        dash_message = {
            "job_ticket_id": f"integration_testing_{base_name}",
            "feature_flags":
            {
                "dash_feature_flag": "on",
                "alma_feature_flag": "on",
                "send_to_drs_feature_flag": "on"
            },
        }
        client.send_task(name="etd-dash-service.tasks.send_to_dash",
                         args=[dash_message], kwargs={},
                         queue=incoming_queue)
        return result

    def get_dash_object(self, identifier):
        rest_url = os.getenv("DASH_REST_URL",
                             "https://dspace6-qai.lib.harvard.edu/rest")
        query_url = f"{rest_url}/items/find-by-metadata-field"
        json_query = {"key": "dc.identifier.other", "value": identifier}
        resp = requests.post(query_url, json=json_query, verify=False)
        return resp.text

    def get_session_key(self):
        rest_url = os.getenv("DASH_REST_URL",
                             "https://dspace6-qai.lib.harvard.edu/rest")
        login_url = f"{rest_url}/login"
        login_email = os.getenv("DASH_LOGIN_EMAIL")
        login_pw = os.getenv("DASH_LOGIN_PW")
        login_info = {"email": login_email, "password": login_pw}
        resp = requests.post(login_url, data=login_info, verify=False)
        return resp.cookies.get('JSESSIONID')

    def cleanup_test_object(self, base_name, schoolcode="gsd"):
        dirname = 'proquest*-' + base_name + '-' + schoolcode
        if glob.glob('/home/etdadm/data/in/' + dirname + '/submission_' + base_name + '.zip'):  # noqa: E501
            for filename in glob.glob('/home/etdadm/data/in/' + dirname + '/*'):  # noqa: E501
                os.remove(filename)
            for filename in glob.glob('/home/etdadm/data/in/' + dirname):  # noqa: E501
                shutil.rmtree(filename)

    def sftp_test_object(self, submission_zip_object, schoolcode="gsd"):
        # proquest2dash test vars
        private_key = os.getenv("PRIVATE_KEY_PATH")
        remoteSite = os.getenv("dropboxServer")
        remoteUser = os.getenv("dropboxUser")
        archiveDir = "archives/" + schoolcode
        incomingDir = "incoming/" + schoolcode
        self.logger.debug(">>> Test object name: {}".
                          format(submission_zip_object))
        with pysftp.Connection(host=remoteSite,
                               username=remoteUser,
                               private_key=private_key) as sftp:
            # remove any existing test object
            if sftp.exists(f"{archiveDir}/{submission_zip_object}"):
                sftp.remove(f"{archiveDir}/{submission_zip_object}")
            # sftp test object to incoming dir
            try:
                sftp.put(f"./testdata/{submission_zip_object}",
                         f"{incomingDir}/{submission_zip_object}")
            except Exception as err:
                self.logger.error(f"SFTP error: {err}")

    # Method to return a random string of 10 digits
    def random_digit_string(self):
        return ''.join(random.choices(string.digits, k=10))

    # Check the number of times a submission has been submitted to dash
    def verify_submission_count(self, identifier):  # noqa: E501
        """
        Verifies the number of times a submission has been submitted to dash.
        If the count does not match expected count, an error is logged and
        recorded in the result dictionary.

        Returns:
            int: The number of times a submission has been submitted to dash.
        """
        resp_text = self.get_dash_object(identifier)
        self.logger.debug(">>> Dash object: " + resp_text)

        count = len(json.loads(resp_text))
        return count

    def replace_pq_id(self, new_pq_id, submission_file_path):
        # Unzip
        directory_to_extract_to = os.path.join(os.path.dirname(
            submission_file_path), 'extracted')
        with zipfile.ZipFile(submission_file_path, 'r') as zip_ref:
            zip_ref.extractall(directory_to_extract_to)

        # Replace in mets.xml
        mets_path = os.path.join(directory_to_extract_to, 'mets.xml')
        tree = ET.parse(mets_path)
        metsroot = tree.getroot()

        namespaces = {'dim': 'http://www.dspace.org/xmlns/dspace/dim'}
        metsroot.find(".//dim:field[@mdschema='dc'][@element='identifier'][@qualifier='other']", namespaces).text = new_pq_id # noqa
        tree.write(mets_path)

        # Delete submission zip
        os.remove(submission_file_path)

        # Zip
        with zipfile.ZipFile(submission_file_path, mode="w") as archive:
            for file in os.listdir(directory_to_extract_to):
                archive.write(os.path.join(directory_to_extract_to,
                                           file), file)
        # Delete extracted directory
        shutil.rmtree(directory_to_extract_to)
