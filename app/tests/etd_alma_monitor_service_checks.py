import os
from celery import Celery
import shutil
import logging
from datetime import datetime
from pymongo import MongoClient
import traceback


class ETDAlmaMonitorServiceChecks():

    def __init__(self):
        self.logger = logging.getLogger('etd_int_tests')

    def monitor_alma_and_invoke_dims(self):
        result = {"num_failed": 0,
                  "tests_failed": [],
                  "info": {}}
        try:
            # Copy test submission file from data dir to ETD 'in' directory
            zip_file = "submission_999999.zip"
            dir_unique_appender = str(int(datetime.now().timestamp()))
            directory_id = "alma_monitor_service_test_" + dir_unique_appender
            copy_result = self.__copy_test_submission(
                zip_file,
                directory_id)
            mongo_result = self.__insert_alma_reccord_in_mongo(directory_id)
            self.__place_queue_message()
            result["num_failed"] = copy_result["num_failed"] + \
                mongo_result["num_failed"]
            result["tests_failed"] = copy_result["tests_failed"]
            result["tests_failed"].append(mongo_result["tests_failed"])
            result["info"] = copy_result["info"]
            result["info"].update(mongo_result["info"])
        except Exception as e:
            self.logger.error(traceback.format_exc())
            result["num_failed"] += 1
            result["tests_failed"].append("Copy failed with exception")
            result["info"].update({"Copy failed with exception":
                                  {"status_code": 500,
                                   "text": str(e)}})
        return result

    def __copy_test_submission(self, zip_file, test_submission_dir_name):
        result = {"num_failed": 0,
                  "tests_failed": [],
                  "info": {}}
        test_dir = os.getenv("TEST_DATA_DIRECTORY")
        test_path = os.path.join(test_dir, zip_file)

        dest_dir = os.getenv("ETD_IN_DIR")
        dest_path = os.path.join(dest_dir, test_submission_dir_name)
        os.makedirs(dest_path, exist_ok=True)
        try:
            shutil.copy(test_path, dest_path)
            if not os.path.isfile(os.path.join(dest_path, zip_file)):
                result["num_failed"] += 1
                result["tests_failed"].append("Copy failed without exception")
                result["info"] = {"Copy failed without exception":
                                  {"status_code": 500,
                                   "text": "File not found at {}".
                                   format(os.path.join(dest_path, zip_file))}}
        except Exception as e:
            self.logger.error(traceback.format_exc())
            result["num_failed"] += 1
            result["tests_failed"].append("Copy failed with exception")
            result["info"] = {"Copy failed with exception":
                              {"status_code": 500,
                               "text": str(e)}}

        return result

    def __insert_alma_reccord_in_mongo(self, directory_id):
        result = {"num_failed": 0,
                  "tests_failed": [], "info": {}}
        # Set up mongo
        mongo_url = os.getenv('MONGO_URL')
        known_pq_id = os.getenv("KNOWN_PQ_ID")
        record = {"proquest_id": known_pq_id,
                  "school_alma_dropbox": "gsd",
                  "alma_submission_status": "ALMA_DROPBOX",
                  "insertion_date": datetime.now().isoformat(),
                  "last_modified_date": datetime.now().isoformat(),
                  "alma_dropbox_submission_date":
                  datetime.now().isoformat(),
                  "directory_id": directory_id}
        try:
            mongo_client = MongoClient(mongo_url, maxPoolSize=1)
            mongo_db = mongo_client[os.getenv("MONGO_DBNAME")]
            collection = mongo_db[os.getenv("MONGO_COLLECTION")]
            collection.insert_one(record)
            mongo_client.close()
        except Exception as err:
            self.logger.error(traceback.format_exc())
            result = {"num_failed": 1,
                      "tests_failed": ["Mongo"],
                      "info": {"Failed Mongo":
                               {"status_code": 500,
                                "text": str(err)}}}
            mongo_client.close()
        return result

    def __place_queue_message(self):
        client = Celery('app')
        client.config_from_object('celeryconfig')
        message = {
            "job_ticket_id": "integration_testing", "integration_test": True,
            "feature_flags":
            {
                "dash_feature_flag": "on",
                "alma_feature_flag": "on",
                "send_to_drs_feature_flag": "on",
                "drs_holding_record_feature_flag": "off"
            }
        }
        queue = os.getenv("ALMA_MONITOR_SERVICE_QUEUE_NAME")
        client.send_task(name="etd-alma-monitor-service.tasks.send_to_drs",
                         args=[message], kwargs={},
                         queue=queue)
