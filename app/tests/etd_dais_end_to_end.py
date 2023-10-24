import os
import os.path
import shutil
from datetime import datetime
import requests
import logging


class ETDDAISEndToEnd():

    def __init__(self):
        self.logger = logging.getLogger('etd_int_tests')

    def end_to_end_test(self, content_model=None):
        result = {"num_failed": 0,
                  "tests_failed": [],
                  "info": {}}

        try:
            # Copy test submission file from data dir to ETD 'in' directory
            if content_model is None:
                dest_path = self.__copy_test_submission()
            else:
                dest_path = self.__copy_test_submission_cm(content_model)
        except Exception as e:
            result["num_failed"] += 1
            result["tests_failed"].append("Copy failed with exception")
            result["info"] = {"Copy failed with exception":
                              {"status_code": 500,
                               "text": str(e)}}
            return result

        payload_data = {}
        # Build DRS Admin MD
        if dest_path:
            payload_data = self.__build_drs_admin_md(dest_path, content_model)
        else:
            result["num_failed"] += 1
            result["tests_failed"].append("Copy failed")
            result["info"] = {"Copy failed":
                              {"status_code": 500,
                               "text": "Copy failed"}}
            return result

        try:
            # Call DIMS
            self.__call_dims(payload_data)
        except Exception as e:
            result["num_failed"] += 1
            result["tests_failed"].append("DIMS call failed")
            result["info"] = {"DIMS Call failed":
                              {"status_code": 500,
                               "text": str(e)}}

        return result

    def __copy_test_submission_cm(self, content_model):
        test_dir = os.getenv("TEST_DATA_DIRECTORY")
        test_path = os.path.join(test_dir, content_model)

        dest_dir = os.getenv("ETD_IN_DIR")
        dest_path = os.path.join(dest_dir, content_model
                                 + "_submission_integration_test")
        os.makedirs(dest_path, exist_ok=True)
        self.logger.debug("Test Path: " + test_path)
        self.logger.debug("Dest Path: " + dest_path)
        try:
            files = os.listdir(test_path)

            for file_name in files:
                dest_path = os.path.join(dest_path, file_name)
                self.logger.debug("File Dest Path: " + dest_path)
                shutil.copy(os.path.join(test_path, file_name), dest_path)
        except Exception:
            return False

        if os.path.isfile(dest_path):
            return dest_path
        return False

    def __copy_test_submission(self):
        raise Exception("NOT YET IMPLEMENTED")
        test_dir = os.getenv("TEST_DATA_DIRECTORY")
        zip_file = "submission_999999.zip"
        test_path = os.path.join(test_dir, zip_file)

        dest_dir = os.getenv("ETD_IN_DIR")
        dest_path = os.path.join(dest_dir,
                                 "submission_integration_test", zip_file)

        try:
            shutil.copy(test_path, dest_path)
        except Exception:
            return False

        if os.path.isfile(dest_path):
            return dest_path
        return False

    def __build_drs_admin_md(self, dest_path, content_model):
        # Create a unique OSN based on the timestamp
        unique_osn = "ETD_TEST_" + content_model + "_" + \
            str(int(datetime.now().timestamp()))

        payload_data = {"package_id": unique_osn,
                        "fs_source_path": dest_path,
                        "s3_path": "",
                        "s3_bucket_name": "",
                        "depositing_application": "ETD",
                        "admin_metadata": {
                            "accessFlag": "N",
                            "contentModel": content_model,
                            "depositingSystem": "ETD",
                            "firstGenerationInDrs": "yes",
                            "usageClass": "LOWUSE",
                            "storageClass": "AR",
                            "ownerCode": "HUL.TEST",
                            "billingCode": "HUL.TEST.BILL_0001",
                            "resourceNamePattern": "{n}",
                            "urnAuthorityPath": "HUL.TEST",
                            "depositAgent": "dimsdts1",
                            "depositAgentEmail": "DTS@HU.onmicrosoft.com",
                            "successEmail": "DTS@HU.onmicrosoft.com",
                            "failureEmail": "DTS@HU.onmicrosoft.com",
                            "successMethod": "all",
                            "original_queue": "test",
                            'task_name': "test",
                            "retry_count": 0,
                            "mmsid": "12345"
                        }
                        }
        return payload_data

    def __call_dims(self, payload_data):

        dims_endpoint = os.getenv('DIMS_ENDPOINT')

        # Call DIMS ingest
        ingest_etd_export = None

        ingest_etd_export = requests.post(
            dims_endpoint + '/ingest',
            json=payload_data,
            verify=False)

        json_ingest_response = ingest_etd_export.json()
        if json_ingest_response["status"] == "failure":
            raise Exception("DIMS Ingest call failed")
