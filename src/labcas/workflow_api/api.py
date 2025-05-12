import logging
from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields
from datetime import datetime
from typing import Dict, List, Optional, Any
from labcas.workflow_api.airflow import AirflowClient

logger = logging.getLogger(__name__)

AIRFLOW_URL = "http://localhost:8080" # TODO: Make this configurable
AIRFLOW_USERNAME = "admin"
AIRFLOW_PASSWORD = "test"

def create_app() -> Flask:
    """Create and configure the Flask application."""

    app = Flask(__name__)
    api = Api(app, title='Science Workflow Execution API',
              description='REST API to list, describe, trigger, and monitor scientific workflows.')

    # Model definitions
    workflow_model = api.model('Workflow', {
        'id': fields.String(example="my_workflow"),
        'description': fields.String(example="This workflow processes satellite imagery.")
    })

    workflow_detail_model = api.model('WorkflowDetail', {
        'id': fields.String(),
        'description': fields.String(),
        'parameters': fields.Raw(),
        'schedule': fields.String(nullable=True)
    })

    run_status_enum = ['queued', 'running', 'success', 'failed']

    run_model = api.model('Run', {
        'run_id': fields.String(),
        'workflow_id': fields.String(),
        'status': fields.String(enum=run_status_enum),
        'start_time': fields.DateTime()
    })

    run_detail_model = api.model('RunDetail', {
        'run_id': fields.String(),
        'workflow_id': fields.String(),
        'status': fields.String(enum=run_status_enum),
        'params': fields.Raw(),
        'results': fields.Raw(nullable=True)
    })

    # Routes
    @api.route('/workflows')
    class WorkflowList(Resource):

        airflow_client = AirflowClient(AIRFLOW_URL, AIRFLOW_USERNAME, AIRFLOW_PASSWORD, mwaa=True)

        @api.marshal_list_with(workflow_model)
        def get(self) -> List[Dict[str, str]]:
            """List available workflows"""
            # TODO: Implement workflow listing logic
            airflow_dags = self.airflow_client.get_dags()['dags']
            logger.debug(f"Airflow DAGs: {airflow_dags}")
            return [{"id": dag["dag_id"], "description": dag["description"]} for dag in airflow_dags]

        

    @api.route('/workflows/<string:id>')
    class Workflow(Resource):
        @api.marshal_with(workflow_detail_model)
        def get(self, id: str) -> Dict[str, Any]:
            """Get workflow description"""
            # TODO: Implement workflow detail retrieval logic
            return {}
        
    @api.route('/workflows/<string:id>/runs')
    class WorkflowRuns(Resource):
        @api.marshal_list_with(run_model)
        def get(self, id: str) -> Dict[str, Any]:
            """Get workflow description"""
            airflow_client = AirflowClient(AIRFLOW_URL, AIRFLOW_USERNAME, AIRFLOW_PASSWORD, mwaa=True)
            runs = airflow_client.get_runs(id)
            # TODO: Implement workflow detail retrieval logic
            return runs

    @api.route('/runs')
    class RunList(Resource):
        @api.expect(api.model('RunRequest', {
            'workflow_id': fields.String(required=True),
            'params': fields.Raw()
        }))
        @api.marshal_with(run_model)
        def post(self) -> Dict[str, Any]:
            """Trigger a workflow run"""
            # Get request payload
            data = request.get_json()
            
            # Extract workflow_id and params from payload
            workflow_id = data.get('workflow_id')
            params = data.get('params', {})
            
            if not workflow_id:
                api.abort(400, "workflow_id is required")
                
            # Initialize airflow client and trigger DAG run
            airflow_client = AirflowClient(AIRFLOW_URL, AIRFLOW_USERNAME, AIRFLOW_PASSWORD, mwaa=True)
            run_id, status = airflow_client.run_dag(workflow_id, params)
            
            # Return run details
            return {
                'workflow_id': workflow_id,
                'run_id': run_id,
                'status': status,
                'start_time': datetime.now()
            }
            


        @api.marshal_list_with(run_model)
        def get(self) -> List[Dict[str, Any]]:
            """List workflow runs"""

            # TODO: Implement run listing logic
            return []

    @api.route('/runs/<string:id>')
    class Run(Resource):
        @api.marshal_with(run_detail_model)
        def get(self, id: str) -> Dict[str, Any]:
            """Get run status and results"""
            # TODO: Implement run detail retrieval logic
            return {}

    return app 