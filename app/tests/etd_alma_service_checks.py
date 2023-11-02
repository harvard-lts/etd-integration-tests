import time
import os
import json
from celery import Celery
import pysftp
import glob
import shutil
import logging
from lib.ltstools import get_date_time_stamp


class ETDAlmaServiceChecks():

    def __init__(self):
        self.logger = logging.getLogger('etd_int_tests')

    def alma_service_test(self):
        self.logger.info(">>> Starting alma service integration test")
        result = {"num_failed": 0,
                  "tests_failed": [],
                  "info": {}}
        incoming_queue = os.environ.get('ALMA_SERVICE_QUEUE_NAME',
                                        'etd_in_storage')

        FEATURE_FLAGS = "feature_flags"
        DASH_FEATURE_FLAG = "dash_feature_flag"
        ALMA_FEATURE_FORCE_UPDATE_FLAG = "alma_feature_force_update_flag"
        ALMA_FEATURE_FLAG = "alma_feature_flag"

        yyyymmdd          = get_date_time_stamp('day')
        xmlCollectionFile = f'AlmaDeliveryTest_{yyyymmdd}.xml'

        client = Celery('app')
        client.config_from_object('celeryconfig')

        self.logger.info(">>> Read message file")
        messagefile = os.environ.get('MESSAGE_FILE', "message.json")
        with open(messagefile) as f:
            messagejson = f.read()
        message = json.loads(messagejson)

        # only run if dash & alma feature flags are on
        if FEATURE_FLAGS in message:
            feature_flags = message[FEATURE_FLAGS]
            if (DASH_FEATURE_FLAG in feature_flags and
                    feature_flags[DASH_FEATURE_FLAG] == "on"):

                message[FEATURE_FLAGS][ALMA_FEATURE_FLAG] == "on"
                message[FEATURE_FLAGS][ALMA_FEATURE_FORCE_UPDATE_FLAG] == "on"

                batch_name = os.getenv('ALMA_BATCH_NAME',
                                       'proquest2023071720-993578-gsd')
                # 1. clear out any old test object
                self.logger.info(">>> Cleanup test object")
                self.cleanup_test_object(batch_name)

                # 2. setup the test object
                self.logger.info(">>> Setup test object")
                self.setup_test_object(batch_name)

                # 3. send the test object to alma
                self.logger.info(">>> Submit test object to alma")
                client.send_task(name="etd-alma-service.tasks.send_to_alma",
                                    args=[message], kwargs={},
                                    queue=incoming_queue)
                sleep_secs = int(os.environ.get('SLEEP_SECS', 30))
                time.sleep(sleep_secs)  # wait for queue

                # 4. put the test object in the dropbox
                self.logger.info(">>> SFTP check Alma export")
                exportExists = False
                try:
                    exportExists = self.sftp_check_export(xmlCollectionFile)
                except Exception as err:
                    result["num_failed"] += 1
                    result["tests_failed"].append("SFTP")
                    result["info"] = {"Alma Dropbox sftp failed":
                                      {"status_code": 500,
                                       "text": str(err)}}
                    self.logger.error(str(err))
                if not exportExists:
                    result["num_failed"] += 1
                    result["tests_failed"].append("ALMA_EXPORT")
                    result["info"] = {"Alma Dropbox export failed":
                                      {"status_code": 500,
                                       "text": "Export not found"}}
                    self.logger.error("Alma Dropbox export failed")

                #5. cleanup the test object from the filesystem
                self.logger.info(">>> Clean test object")
                self.cleanup_test_object(batch_name)

            else:
                client.send_task(name="etd-alma-service.tasks.send_to_alma",
                                 args=[message], kwargs={},
                                 queue=incoming_queue)

                sleep_secs = int(os.environ.get('SLEEP_SECS', 2))

                time.sleep(sleep_secs)  # wait for queue

        return result


    def cleanup_test_object(self, base_name):
        if os.path.exists('/home/etdadm/data/in/' + base_name):
            for filename in glob.glob('/home/etdadm/data/in/' + base_name + '/*'):  # noqa: E501
                os.remove(filename)
            for filename in glob.glob('/home/etdadm/data/in/' + base_name):  # noqa: E501
                shutil.rmtree(filename)
        if os.path.exists('/home/etdadm/data/out/' + base_name):
            for filename in glob.glob('/home/etdadm/data/out/' + base_name + '/*'):  # noqa: E501
                os.remove(filename)
            for filename in glob.glob('/home/etdadm/data/out/' + base_name):  # noqa: E501
                shutil.rmtree(filename)
    

    def setup_test_object(self, base_name):
        if not os.path.exists('/home/etdadm/data/in/' + base_name):
            os.mkdir('/home/etdadm/data/in/' + base_name)
        shutil.copy2('/home/etdadm/testdata/alma/in/' + base_name +
                     '/mets.xml', '/home/etdadm/data/in/' + base_name) # noqa: E501
        if not os.path.exists('/home/etdadm/data/out/' + base_name):
            os.mkdir('/home/etdadm/data/out/' + base_name)
        shutil.copy2('/home/etdadm/testdata/alma/out/' + base_name +
                     '/mapfile', '/home/etdadm/data/out/' + base_name) # noqa: E501

    def sftp_check_export(self, base_name):
        # alma service test vars
        private_key = os.getenv("ALMA_PRIVATE_KEY_PATH")
        remoteSite = os.getenv("ALMA_DROPBOX_SERVER")
        remoteUser = os.getenv("ALMA_DROPBOX_USER")
        incomingDir = "incoming/"
        exportExists = False
 
        with pysftp.Connection(host=remoteSite,
                               username=remoteUser,
                               private_key=private_key) as sftp:
            try:
                if sftp.exists(f"{incomingDir}/{base_name}"):
                    # this file should be deleted. keep it for now so QA can
                    # review it directly.
                    # sftp.remove(f"{incomingDir}/{base_name}")
                    exportExists = True
            except Exception as err:
                self.logger.error(f"SFTP error: {err}")
        return exportExists
