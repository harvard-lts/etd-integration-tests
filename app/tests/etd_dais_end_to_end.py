import os
import os.path
import shutil
from datetime import datetime
from datetime import timedelta
import jwt
import hashlib
import jcs
import requests
import traceback
import logging
from logging.handlers import TimedRotatingFileHandler

LOG_FILE_BACKUP_COUNT = 1
LOG_ROTATION = "midnight"
log_level = os.getenv("LOG_LEVEL", "DEBUG")
log_dir = os.getenv("LOG_DIR", "/home/etdadm/logs")
log_file_path = os.path.join(log_dir, "int_tests.log")
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
file_handler = TimedRotatingFileHandler(
    filename=log_file_path,
    when=LOG_ROTATION,
    backupCount=LOG_FILE_BACKUP_COUNT
)
logger = logging.getLogger()
logger.addHandler(file_handler)
file_handler.setFormatter(formatter)
logger.setLevel(log_level)

class ETDDAISEndToEnd():

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
            result["tests_failed"].append("Copy failed with exception".format(dest_path))
            result["info"] = {"Copy failed with exception".format(dest_path):
                              {"status_code": 500,
                               "text": str(e)}}
            return result

        payload_data = {}
        # Build DRS Admin MD
        if dest_path:
            payload_data = self.__build_drs_admin_md(dest_path, content_model)
        else:
            result["num_failed"] += 1
            result["tests_failed"].append("Copy failed".format(dest_path))
            result["info"] = {"Copy failed".format(dest_path):
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
        dest_path = os.path.join(dest_dir, content_model + "_submission_integration_test")
        os.makedirs(dest_path, exist_ok=True)
        logger.debug("Test Path: " + test_path)
        logger.debug("Dest Path: " + dest_path)
        try:
            files = os.listdir(test_path)

            for file_name in files:
                dest_path = os.path.join(dest_path, file_name)
                logger.debug("File Dest Path: " + dest_path)
                shutil.copy(os.path.join(test_path, file_name), dest_path)  
        except:
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
        dest_path = os.path.join(dest_dir, "submission_integration_test", zip_file)

        try:
            shutil.copy(test_path, dest_path)
        except:
            return False

        if os.path.isfile(dest_path):
            return dest_path
        return False
    

    def __build_drs_admin_md(self, dest_path, content_model):
        # Create a unique OSN based on the timestamp
        unique_osn = "ETD_TEST_" + str(int(datetime.now().timestamp()))

        payload_data = {"package_id": unique_osn,
                    "fs_source_path": dest_path,
                    "s3_path": "",
                    "s3_bucket_name": "",
                    "depositing_application": "ETD",
                    "admin_metadata": {
                        "accessFlag": "N",
                        "contentModel": content_model,
                        "depositingSystem": "ETD",
                        "firstGenerationInDrs": "Y",
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
        jwt_private_key_path = os.getenv('JWT_PRIVATE_KEY_PATH')
        jwt_expiration = int(os.getenv('JWT_EXPIRATION'))
        dims_endpoint = os.getenv('DIMS_ENDPOINT')

        with open(jwt_private_key_path) as jwt_private_key_file:
            jwt_private_key = jwt_private_key_file.read()


        # calculate iat and exp values
        current_datetime = datetime.now()
        current_epoch = int(current_datetime.timestamp())
        expiration = current_datetime + timedelta(seconds=jwt_expiration)

        # get request_body hash
        request_body = jcs.canonicalize(payload_data).decode()
        bodySHA256Hash = hashlib.sha256(request_body.encode()).hexdigest()

        # generate JWT token
        jwt_token = jwt.encode(
            payload={'iss': 'ETD', 'iat': current_epoch, 'exp': int(expiration.timestamp()),
                    'bodySHA256Hash': bodySHA256Hash},
            key=jwt_private_key,
            algorithm='RS256',
            headers={"alg": "RS256", "typ": "JWT", "kid": "defaultETD"}
        )

        headers = {"Authorization": "Bearer " + jwt_token}

        # Call DIMS ingest
        ingest_etd_export = None

        ingest_etd_export = requests.post(
            dims_endpoint + '/ingest',
            headers=headers,
            json=payload_data,
            verify=False)
        
        json_ingest_response = ingest_etd_export.json()
        if json_ingest_response["status"] == "failure":
            raise Exception("DIMS Ingest call failed")
