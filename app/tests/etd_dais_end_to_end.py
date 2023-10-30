import os
import os.path
import shutil
from datetime import datetime
import requests
import logging


class ETDDAISEndToEnd():

    def __init__(self):
        self.logger = logging.getLogger('etd_int_tests')

    def end_to_end_test(self):
        result = {"num_failed": 0,
                  "tests_failed": [],
                  "info": {}}

        try:
            # Copy test submission file from data dir to ETD 'in' directory
            dest_path = self.__copy_test_submission()
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
            payload_data = self.__build_drs_admin_md(dest_path)
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

    def __copy_test_submission(self):
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
        osn_unique_appender = str(int(datetime.now().timestamp()))

        thesis_name = "0521Yolandayuanlupeng_finalNaming Expeditor.pdf"
        license_name = "setup_2E592954-F85C-11EA-ABB1-E61AE629DA94.pdf"
        file_info = {
            thesis_name: {
                "modified_file_name":
                "0521Yolandayuanlupeng_finalNaming_Expeditor.pdf",
                "file_role": "ARCHIVAL_MASTER",
                "object_role": "THESIS",
                "object_osn": "ETD_THESIS_test_2023-05_PQ_TEST1234_"
                + osn_unique_appender,
                "file_osn": "ETD_THESIS_test_2023-05_PQ_TEST1234_"
                + osn_unique_appender + "_1"
            },
            license_name: {
                "modified_file_name":
                "setup_2E592954-F85C-11EA-ABB1-E61AE629DA94.pdf",
                "file_role": "LICENSE",
                "object_role": "LICENSE",
                "object_osn": "ETD_LICENSE_test_2023-05_PQ_TEST1234_"
                + osn_unique_appender,
                "file_osn": "ETD_LICENSE_test_2023-05_PQ_TEST1234_"
                + osn_unique_appender + "_1"
            },
            "mets.xml": {
                "modified_file_name": "mets.xml",
                "file_role": "DOCUMENTATION",
                "object_role": "DOCUMENTATION",
                "object_osn": "ETD_DOCUMENTATION_test_2023-05_PQ_TEST1234_"
                + osn_unique_appender,
                "file_osn": "ETD_DOCUMENTATION_test_2023-05_PQ_TEST1234_"
                + osn_unique_appender + "_1"
            }
        }
        payload_data = {"package_id": "ETD_TESTING",
                        "fs_source_path": dest_path,
                        "s3_path": "",
                        "s3_bucket_name": "",
                        "depositing_application": "ETD",
                        "admin_metadata": {
                            "depositingSystem": "ETD",
                            "ownerCode": "HUL.TEST",
                            "billingCode": "HUL.TEST.BILL_0001",
                            "original_queue": "test",
                            'task_name': "test",
                            "retry_count": 0,
                            "mmsid": "12345",
                            "dash_id": "30522803",
                            "pq_id": "PQ-TEST1234",
                            "alma_id": "99156631569803941",
                            "file_info": file_info
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
