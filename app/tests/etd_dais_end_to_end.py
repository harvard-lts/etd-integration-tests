import os
import os.path
import shutil
from datetime import datetime
import requests
import logging


class ETDDAISEndToEnd():

    def __init__(self):
        self.logger = logging.getLogger('etd_int_tests')

    def end_to_end_documentation_test(self):
        """
        This function performs an end-to-end test for a basic ETD.
        It copies a test submission file from the data directory to the
        ETD 'in' directory, builds DRS Admin MD for documentation, and calls
        DIMS to complete the process. If any of these steps fail, the
        function returns a dictionary with information about the failure.

        Returns:
            A dictionary with the following keys:
            - num_failed: the number of failed tests (0 if all tests passed)
            - tests_failed: a list of failed test names
            - info: a dictionary with information about any failures
        """
        result = {"num_failed": 0,
                  "tests_failed": [],
                  "info": {}}

        try:
            # Copy test submission file from data dir to ETD 'in' directory
            zip_file = "submission_999999.zip"
            dest_path = self.__copy_test_submission(
                zip_file,
                "end_to_end_documentation_test")
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
            payload_data = self. \
                __build_drs_admin_md_for_documentation(dest_path)
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

    def end_to_end_images_test(self):
        """
        This function performs an end-to-end test for the ETD system using
        image files. It copies a test submission file from the data directory
        to the ETD 'in' directory, builds DRS Admin MD for the images, and
        calls DIMS. It returns a dictionary with the number of failed tests,
        a list of failed tests, and additional information about the failed
        tests if any.

        Returns:
            dict: A dictionary with the following keys:
                - num_failed (int): The number of failed tests.
                - tests_failed (list): A list of failed tests.
                - info (dict): Additional information about the failed tests
                if any.
        """
        result = {"num_failed": 0,
                  "tests_failed": [],
                  "info": {}}

        try:
            # Copy test submission file from data dir to ETD 'in' directory
            zip_file = "submission_five_gifs.zip"
            dest_path = self.__copy_test_submission(
                zip_file, "end_to_end_images_test")
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
            payload_data = self. \
                __build_drs_admin_md_for_images(dest_path)
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

    def end_to_end_opaque_gif_test(self):
        """
        This function performs an end-to-end test for the ETD system using
        opaque and image files. It copies a test submission file from the
        data directory to the ETD 'in' directory, builds DRS Admin MD for
        the opaque and images, and calls DIMS. It returns a dictionary with
        the number of failed tests, a list of failed tests, and additional
        information about the failed tests if any.

        Returns:
            dict: A dictionary with the following keys:
                - num_failed (int): The number of failed tests.
                - tests_failed (list): A list of failed tests.
                - info (dict): Additional information about the failed tests
                if any.
        """
        result = {"num_failed": 0,
                  "tests_failed": [],
                  "info": {}}

        try:
            # Copy test submission file from data dir to ETD 'in' directory
            zip_file = "submission_opaque_gif.zip"
            dest_path = self.__copy_test_submission(
                zip_file, "end_to_end_opaque_images_test")
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
            payload_data = self. \
                __build_drs_admin_md_for_opaque_gif(dest_path)
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

    def end_to_end_audio_test(self):
        """
        This function performs an end-to-end test for the ETD system using
        audio files. It copies a test submission file from the data directory
        to the ETD 'in' directory, builds DRS Admin MD for the audio,
        and calls DIMS. It returns a dictionary with the number of
        failed tests, a list of failed tests, and additional information
        about the failed tests if any.

        Returns:
            dict: A dictionary with the following keys:
                - num_failed (int): The number of failed tests.
                - tests_failed (list): A list of failed tests.
                - info (dict): Additional information about the failed tests
                if any.
        """
        result = {"num_failed": 0,
                  "tests_failed": [],
                  "info": {}}

        try:
            # Copy test submission file from data dir to ETD 'in' directory
            zip_file = "submission_audio.zip"
            dest_path = self.__copy_test_submission(
                zip_file, "end_to_end_audio_test")
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
            payload_data = self. \
                __build_drs_admin_md_for_audio(dest_path)
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

    def __copy_test_submission(self, zip_file, test_submission_dir_name):
        test_dir = os.getenv("TEST_DATA_DIRECTORY")
        test_path = os.path.join(test_dir, zip_file)

        dest_dir = os.getenv("ETD_IN_DIR")
        dest_path = os.path.join(dest_dir, test_submission_dir_name)
        os.makedirs(dest_path, exist_ok=True)
        try:
            shutil.copy(test_path, dest_path)
        except Exception:
            return False

        if os.path.isfile(os.path.join(dest_path, zip_file)):
            return os.path.join(dest_path, zip_file)
        return False

    def __build_drs_admin_md_for_documentation(self, dest_path):
        # Create a unique OSN based on the timestamp
        osn_unique_appender = str(int(datetime.now().timestamp()))

        thesis_name = "0521Yolandayuanlupeng_finalNaming Expeditor.pdf"
        license_name = "setup_2E592954-F85C-11EA-ABB1-E61AE629DA94.pdf"
        file_info = {
            thesis_name: {
                "modified_file_name":
                "0521Yolandayuanlupeng_finalNaming_Expeditor.pdf",
                "object_role": "THESIS",
                "object_osn": "ETD_THESIS_test_2023-05_PQ_30522803_"
                + osn_unique_appender,
                "file_osn": "ETD_THESIS_test_2023-05_PQ_30522803_"
                + osn_unique_appender + "_1"
            },
            license_name: {
                "modified_file_name":
                "setup_2E592954-F85C-11EA-ABB1-E61AE629DA94.pdf",
                "object_role": "LICENSE",
                "object_osn": "ETD_LICENSE_test_2023-05_PQ_30522803_"
                + osn_unique_appender,
                "file_osn": "ETD_LICENSE_test_2023-05_PQ_30522803_"
                + osn_unique_appender + "_1"
            },
            "mets.xml": {
                "modified_file_name": "mets.xml",
                "object_role": "DOCUMENTATION",
                "object_osn": "ETD_DOCUMENTATION_test_2023-05_PQ_30522803_"
                + osn_unique_appender,
                "file_osn": "ETD_DOCUMENTATION_test_2023-05_PQ_30522803_"
                + osn_unique_appender + "_1"
            }
        }
        payload_data = {"package_id": "ETD_TESTING_" + osn_unique_appender,
                        "fs_source_path": dest_path,
                        "s3_path": "",
                        "s3_bucket_name": "",
                        "depositing_application": "ETD",
                        "admin_metadata": {
                            "depositingSystem": "ETD",
                            "ownerCode": "HUL.TEST",
                            "billingCode": "HUL.TEST.BILL_0001",
                            "urnAuthorityPath": "HUL.TEST",
                            "original_queue": "test",
                            'task_name': "test",
                            "retry_count": 0,
                            "mmsid": "12345",
                            "dash_id": "TEST1234",
                            "pq_id": "PQ-30522803",
                            "alma_id": "99156631569803941",
                            "file_info": file_info
                        }
                        }
        return payload_data

    def __build_drs_admin_md_for_opaque_gif(self, dest_path):
        # Create a unique OSN based on the timestamp
        timestamp_appender = str(int(datetime.now().timestamp()))

        thesis_name = "Alfred_S_MArchI_F21 Thesis.pdf"
        license_name = "setup_2E592954-F85C-11EA-ABB1-E61AE629DA94.pdf"
        osn_unique_appender = "gsd_2022-05_PQ_28963877_" \
            + timestamp_appender
        file_info = {
            thesis_name: {
                "modified_file_name":
                "Alfred_S_MArchI_F21_Thesis.pdf",
                "object_role": "THESIS",
                "object_osn": "ETD_THESIS_" + osn_unique_appender,
                "file_osn": "ETD_THESIS_" + osn_unique_appender + "_1"
            },
            license_name: {
                "modified_file_name":
                "setup_2E592954-F85C-11EA-ABB1-E61AE629DA94.pdf",
                "object_role": "LICENSE",
                "object_osn": "ETD_LICENSE_" + osn_unique_appender,
                "file_osn": "ETD_LICENSE_" + osn_unique_appender + "_1"
            },
            "mets.xml": {
                "modified_file_name": "mets.xml",
                "object_role": "DOCUMENTATION",
                "object_osn": "ETD_DOCUMENTATION_" + osn_unique_appender,
                "file_osn": "ETD_DOCUMENTATION_" + osn_unique_appender + "_1"
            },
            "Plan Gifs.zip": {
                "modified_file_name": "Plan_Gifs.zip",
                "object_role": "THESIS_SUPPLEMENT",
                "object_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_1",
                "file_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_1_1"
            },
            "Notation Gifs.zip": {
                "modified_file_name": "Notation_Gifs.zip",
                "object_role": "THESIS_SUPPLEMENT",
                "object_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_2",
                "file_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_2_1"
            },
            "Dance Gifs.zip": {
                "modified_file_name": "Dance_Gifs.zip",
                "object_role": "THESIS_SUPPLEMENT",
                "object_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_3",
                "file_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_3_1"
            },
            "Alfred_S_Model gif.gif": {
                "modified_file_name": "Alfred_S_Model_gif.gif",
                "object_role": "THESIS_SUPPLEMENT",
                "object_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_4",
                "file_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_4_1"
            }
        }
        payload_data = {"package_id": "ETD_TESTING_" + timestamp_appender,
                        "fs_source_path": dest_path,
                        "s3_path": "",
                        "s3_bucket_name": "",
                        "depositing_application": "ETD",
                        "admin_metadata": {
                            "depositingSystem": "ETD",
                            "ownerCode": "HUL.TEST",
                            "billingCode": "HUL.TEST.BILL_0001",
                            "urnAuthorityPath": "HUL.TEST",
                            "original_queue": "test",
                            'task_name': "test",
                            "retry_count": 0,
                            "mmsid": "12345",
                            "dash_id": "TEST1234",
                            "pq_id": "PQ-28963877",
                            "alma_id": "99156631569803941",
                            "file_info": file_info
                        }
                        }
        return payload_data

    def __build_drs_admin_md_for_images(self, dest_path):
        # Create a unique OSN based on the timestamp
        timestamp_appender = str(int(datetime.now().timestamp()))

        thesis_name = "20210524_Thesis Archival Submission_JB Signed.pdf"
        license_name = "setup_2E592954-F85C-11EA-ABB1-E61AE629DA94.pdf"
        osn_unique_appender = "test_2021-05_PQ_28542548_" + timestamp_appender
        file_info = {
            thesis_name: {
                "modified_file_name":
                "20210524_Thesis_Archival_Submission_JB_Signed.pdf",
                "object_role": "THESIS",
                "object_osn": "ETD_THESIS_" + osn_unique_appender,
                "file_osn": "ETD_THESIS_" + osn_unique_appender + "_1"
            },
            license_name: {
                "modified_file_name":
                "setup_2E592954-F85C-11EA-ABB1-E61AE629DA94.pdf",
                "object_role": "LICENSE",
                "object_osn": "ETD_LICENSE_" + osn_unique_appender,
                "file_osn": "ETD_LICENSE_" + osn_unique_appender + "_1"
            },
            "mets.xml": {
                "modified_file_name": "mets.xml",
                "object_role": "DOCUMENTATION",
                "object_osn": "ETD_DOCUMENTATION_" + osn_unique_appender,
                "file_osn": "ETD_DOCUMENTATION_" + osn_unique_appender + "_1"
            },
            "GIF_01_SlabShift.gif": {
                "modified_file_name": "GIF_01_SlabShift.gif",
                "object_role": "THESIS_SUPPLEMENT",
                "object_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_1",
                "file_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_1_1"
            },
            "GIF_02_Facade1NE.gif": {
                "modified_file_name": "GIF_02_Facade1NE.gif",
                "object_role": "THESIS_SUPPLEMENT",
                "object_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_2",
                "file_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_2_1"
            },
            "GIF_03_Facade2SW.gif": {
                "modified_file_name": "GIF_03_Facade2SW.gif",
                "object_role": "THESIS_SUPPLEMENT",
                "object_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_3",
                "file_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_3_1"
            },
            "GIF_04_Room_1.Gar.gif": {
                "modified_file_name": "GIF_04_Room_1.Gar.gif",
                "object_role": "THESIS_SUPPLEMENT",
                "object_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_4",
                "file_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_4_1"
            },
            "GIF_05_Room_2.TwoLiv.gif": {
                "modified_file_name": "GIF_05_Room_2.TwoLiv.gif",
                "object_role": "THESIS_SUPPLEMENT",
                "object_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_5",
                "file_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_5_1"
            }
        }
        payload_data = {"package_id": "ETD_TESTING_" + timestamp_appender,
                        "fs_source_path": dest_path,
                        "s3_path": "",
                        "s3_bucket_name": "",
                        "depositing_application": "ETD",
                        "admin_metadata": {
                            "depositingSystem": "ETD",
                            "ownerCode": "HUL.TEST",
                            "billingCode": "HUL.TEST.BILL_0001",
                            "urnAuthorityPath": "HUL.TEST",
                            "original_queue": "test",
                            'task_name': "test",
                            "retry_count": 0,
                            "mmsid": "12345",
                            "dash_id": "TEST1234",
                            "pq_id": "PQ-28542548",
                            "alma_id": "99156631569803941",
                            "file_info": file_info
                        }
                        }
        return payload_data

    def __build_drs_admin_md_for_audio(self, dest_path):
        # Create a unique OSN based on the timestamp
        timestamp_appender = str(int(datetime.now().timestamp()))

        thesis_name = "MLA Thesis_Auger_Catherine_May2023.pdf"
        license_name = "setup_2E592954-F85C-11EA-ABB1-E61AE629DA94.pdf"
        osn_unique_appender = "gsd_2023-05_PQ_30494273_" \
            + timestamp_appender
        file_info = {
            thesis_name: {
                "modified_file_name":
                "MLA_Thesis_Auger_Catherine_May2023.pdf",
                "object_role": "THESIS",
                "object_osn": "ETD_THESIS_" + osn_unique_appender,
                "file_osn": "ETD_THESIS_" + osn_unique_appender + "_1"
            },
            license_name: {
                "modified_file_name":
                "setup_2E592954-F85C-11EA-ABB1-E61AE629DA94.pdf",
                "object_role": "LICENSE",
                "object_osn": "ETD_LICENSE_" + osn_unique_appender,
                "file_osn": "ETD_LICENSE_" + osn_unique_appender + "_1"
            },
            "mets.xml": {
                "modified_file_name": "mets.xml",
                "object_role": "DOCUMENTATION",
                "object_osn": "ETD_DOCUMENTATION_" + osn_unique_appender,
                "file_osn": "ETD_DOCUMENTATION_" + osn_unique_appender + "_1"
            },
            "Gamelan_Islam.mp3": {
                "modified_file_name": "Gamelan_Islam.mp3",
                "object_role": "THESIS_SUPPLEMENT",
                "object_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_1",
                "file_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_1_1"
            },
            "Harry Styles.mp3": {
                "modified_file_name": "Harry_Styles.mp3",
                "object_role": "THESIS_SUPPLEMENT",
                "object_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_2",
                "file_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_2_1"
            },
            "Jalan Raya Ubud.mp3": {
                "modified_file_name": "Jalan_Raya_Ubud.mp3",
                "object_role": "THESIS_SUPPLEMENT",
                "object_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_3",
                "file_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_3_1"
            },
            "Kuningan.mp3": {
                "modified_file_name": "Kuningan.mp3",
                "object_role": "THESIS_SUPPLEMENT",
                "object_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_4",
                "file_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_4_1"
            },
            "Monkey Forest.mp3": {
                "modified_file_name": "Monkey_Forest.mp3",
                "object_role": "THESIS_SUPPLEMENT",
                "object_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_5",
                "file_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_5_1"
            },
            "Pasar Goris.mp3": {
                "modified_file_name": "Pasar_Goris.mp3",
                "object_role": "THESIS_SUPPLEMENT",
                "object_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_6",
                "file_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_6_1"
            },
            "The Pipe.mp3": {
                "modified_file_name": "The_Pipe.mp3",
                "object_role": "THESIS_SUPPLEMENT",
                "object_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_7",
                "file_osn": "ETD_SUPPLEMENT_" + osn_unique_appender + "_7_1"
            }
        }
        payload_data = {"package_id": "ETD_TESTING_" + timestamp_appender,
                        "fs_source_path": dest_path,
                        "s3_path": "",
                        "s3_bucket_name": "",
                        "depositing_application": "ETD",
                        "admin_metadata": {
                            "depositingSystem": "ETD",
                            "ownerCode": "HUL.TEST",
                            "billingCode": "HUL.TEST.BILL_0001",
                            "urnAuthorityPath": "HUL.TEST",
                            "original_queue": "test",
                            'task_name': "test",
                            "retry_count": 0,
                            "dash_id": "TEST1234",
                            "pq_id": "PQ-30494273",
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
