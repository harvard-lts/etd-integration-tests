from flask_restx import Resource, Api
import os
import json

from app.tests.connectivity_checks import ConnectivityChecks
from app.tests.etd_dash_service_checks import ETDDashServiceChecks
from app.tests.etd_dais_end_to_end import ETDDAISEndToEnd


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
        # Mongo
        mongo_result = connectivityChecks.mongodb_connectivity_test()
        result["num_failed"] += mongo_result["num_failed"]
        if len(mongo_result["tests_failed"]) > 0:
            result["tests_failed"].append(mongo_result["tests_failed"])
        result["info"] = result["info"] | mongo_result["info"]

        # DASH
        dash_result = connectivityChecks.dash_connectivity_test()
        result["num_failed"] += dash_result["num_failed"]
        if len(dash_result["tests_failed"]) > 0:
            result["tests_failed"].append(dash_result["tests_failed"])
        result["info"] = result["info"] | dash_result["info"]

        # DIMS
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

    @app.route('/integration')
    def integration_test():
        # Should we save this for the end-to-end?
        result = {"num_failed": 0,
                  "tests_failed": [], "info": {}}

        # For now call all tests since the endpoints haven't
        # been updated in the services yet.
        res1 = connectivity()
        res2 = etd_dash_service_testing()
        res1_json = json.loads(res1)
        res2_json = json.loads(res2)
        result["num_failed"] = res1_json["num_failed"] \
            + res2_json["num_failed"]
        if len(res1_json["tests_failed"]) > 0:
            result["tests_failed"].append(res1_json["tests_failed"])
        if len(res2_json["tests_failed"]) > 0:
            result["tests_failed"].append(res2_json["tests_failed"])
        result["info"] = result["info"] | res1_json["info"] | res2_json["info"]

        return json.dumps(result)

    @app.route('/etd_basic_test')
    def etd_test():
        result = {"num_failed": 0,
                  "tests_failed": [], "info": {}}

        dais_end_to_end_image = ETDDAISEndToEnd()
        end_to_end_result = dais_end_to_end_image \
            .end_to_end_documentation_test()
        result["num_failed"] = end_to_end_result["num_failed"]
        if len(end_to_end_result["tests_failed"]) > 0:
            result["tests_failed"].append(end_to_end_result["tests_failed"])
        result["info"] = result["info"] | end_to_end_result["info"]

        return json.dumps(result)

    @app.route('/etd_with_images_test')
    def etd_with_images_test():
        result = {"num_failed": 0,
                  "tests_failed": [], "info": {}}

        dais_end_to_end_image = ETDDAISEndToEnd()
        end_to_end_result = dais_end_to_end_image.end_to_end_images_test()
        result["num_failed"] = end_to_end_result["num_failed"]
        if len(end_to_end_result["tests_failed"]) > 0:
            result["tests_failed"].append(end_to_end_result["tests_failed"])
        result["info"] = result["info"] | end_to_end_result["info"]

        return json.dumps(result)

    @app.route('/etd_with_opaque_test')
    def etd_with_opaque_and_image_test():
        result = {"num_failed": 0,
                  "tests_failed": [], "info": {}}

        dais_end_to_end_image = ETDDAISEndToEnd()
        end_to_end_result = dais_end_to_end_image.end_to_end_opaque_gif_test()
        result["num_failed"] = end_to_end_result["num_failed"]
        if len(end_to_end_result["tests_failed"]) > 0:
            result["tests_failed"].append(end_to_end_result["tests_failed"])
        result["info"] = result["info"] | end_to_end_result["info"]

        return json.dumps(result)

    @app.route('/etd_with_audio_test')
    def etd_with_audio_test():
        result = {"num_failed": 0,
                  "tests_failed": [], "info": {}}

        dais_end_to_end_image = ETDDAISEndToEnd()
        end_to_end_result = dais_end_to_end_image.end_to_end_audio_test()
        result["num_failed"] = end_to_end_result["num_failed"]
        if len(end_to_end_result["tests_failed"]) > 0:
            result["tests_failed"].append(end_to_end_result["tests_failed"])
        result["info"] = result["info"] | end_to_end_result["info"]

        return json.dumps(result)
