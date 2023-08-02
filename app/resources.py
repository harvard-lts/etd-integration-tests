import time
from flask_restx import Resource, Api
import os
import json
from celery import Celery

from app.tests.connectivity_checks import ConnectivityChecks
from app.tests.etd_dash_service_checks import ETDDashServiceChecks

def define_resources(app):
    api = Api(app, version='1.0', title='ETD Integration Tests',
              description='This project contains the integration' +
                          'tests for the ETD project')
    dashboard = api.namespace('/',
                              description="This project contains " +
                              "the integration tests for " +
                              "the ETD project")


    # Version / Heartbeat route
    @dashboard.route('/version', endpoint="version", methods=['GET'])
    class Version(Resource):

        def get(self):
            version = os.environ.get('APP_VERSION', "NOT FOUND")
            return {"version": version}

    @app.route('/connectivity')
    def connectivity():
        result = {"num_failed": 0,
                  "tests_failed": [], "info": {}}
        
        connectivityChecks = ConnectivityChecks()
        #Mongo
        mongo_result = connectivityChecks.mongodb_connectivity_test()
        result["num_failed"] += mongo_result["num_failed"]
        if len(mongo_result["tests_failed"]) > 0:
            result["tests_failed"].append(mongo_result["tests_failed"])
        result["info"] = result["info"] | mongo_result["info"]
        
        #DASH
        dash_result = connectivityChecks.dash_connectivity_test()
        result["num_failed"] += dash_result["num_failed"]
        if len(dash_result["tests_failed"]) > 0:
            result["tests_failed"].append(dash_result["tests_failed"])
        result["info"] = result["info"] | dash_result["info"]
        
        #DIMS
        dims_result = connectivityChecks.dims_connectivity_test()
        result["num_failed"] += dims_result["num_failed"]
        if len(dims_result["tests_failed"]) > 0:
            result["tests_failed"].append(dims_result["tests_failed"])
        result["info"] = result["info"] | dims_result["info"]
        
        return json.dumps(result)
    
    @app.route('/dash_service')
    def etd_dash_service_testing():
        result = {"num_failed": 0,
                  "tests_failed": [], "info": {}}
        
        etdDashServiceChecks = ETDDashServiceChecks()
        deposit_result = etdDashServiceChecks.dash_deposit_test()
        result["num_failed"] = deposit_result["num_failed"]
        if len(deposit_result["tests_failed"]) > 0:
            result["tests_failed"].append(deposit_result["tests_failed"])
        result["info"] = result["info"] | deposit_result["info"]
        
        return json.dumps(result)


    # Should we save this for the end-to-end?    
    @app.route('/integration')
    def integration_test():
        esult = {"num_failed": 0,
                  "tests_failed": [], "info": {}}

        

        return json.dumps(result)
