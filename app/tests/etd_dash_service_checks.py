import time
import os
import json
from celery import Celery
import pysftp
import glob
import shutil

class ETDDashServiceChecks():
    
    def dash_deposit_test(self):
        result = {"num_failed": 0,
                  "tests_failed": [], "info": {}}
        incoming_queue = os.environ.get('FIRST_QUEUE_NAME', 'etd_submission_ready')
        completed_queue = os.environ.get('LAST_QUEUE_NAME', 'etd_in_storage')

        # proquest2dash test vars
        private_key = os.getenv("PRIVATE_KEY_PATH")
        remoteSite = os.getenv("dropboxServer")
        remoteUser = os.getenv("dropboxUser")
        archiveDir = "archives/gsd"
        incomingDir = "incoming/gsd"
        zipFile = "submission_999999.zip"

        # Send a simple task (create and send in 1 step)
        # res = client.send_task('tasks.tasks.do_task',
        # args=[{"job_ticket_id":"123","hello":"world"}],
        # kwargs={}, queue=incoming_queue)
        # read from 'final_queue' to see that it went through the pipeline
        messagefile = os.environ.get('MESSAGE_FILE', "message.json")
        with open(messagefile) as f:
            messagejson = f.read()
        message = json.loads(messagejson)
        client = Celery('app')
        client.config_from_object('celeryconfig')

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
            result["info"] = {"Proquest Dropbox sftp failed": {"status_code": 500,
                                                      "text": str(err)}}

        client.send_task(name="etd-dash-service.tasks.send_to_dash",
                         args=[message], kwargs={}, queue=incoming_queue)

        sleep_secs = int(os.environ.get('SLEEP_SECS', 2))

        time.sleep(sleep_secs)  # wait for queue

        if not glob.glob('/home/etdadm/data/in/proquest*-999999-gsd/submission_999999.zip'):  # noqa: E501
            result["num_failed"] += 1
            result["tests_failed"].append("DATA IN")
            result["info"] = result["info"] | {"Failed file check": {"status_code": 500,
                                           "text": "No submission found"}}
        else:
            for filename in glob.glob('/home/etdadm/data/in/proquest*-999999-gsd/*'):  # noqa: E501
                os.remove(filename)
            for filename in glob.glob('/home/etdadm/data/in/proquest*-999999-gsd'):  # noqa: E501
                shutil.rmtree(filename)
                
        return result

        
