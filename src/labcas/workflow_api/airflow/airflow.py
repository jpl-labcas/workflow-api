import requests
from requests.auth import HTTPBasicAuth
import logging

logger = logging.getLogger(__name__)

class AirflowClient:

    def __init__(self, airflow_url: str, username: str, password: str, mwaa: bool = True):
        self.airflow_baseurl = airflow_url
        self.username = username
        self.password = password
        self.mwaa = mwaa
        self.session = requests.Session()
        self.request_kwargs = {}
        if self.mwaa:
            self.__ui_login()
        else:
            token = self.__get_jwt_token()
            self.request_kwargs = {"headers": {"Authorization": f"Bearer {token}"}}


    def __ui_login(self):
        url = f"{self.airflow_baseurl}/login"
        response = self.session.post(url, data={"username": self.username, "password": self.password})
        logger.info(response.status_code)
        logger.info(f"Response: {response.text}")


    def __get_jwt_token(self):
        url = f"{self.airflow_baseurl}/api/v1/auth/login"
        response = self.session.post(url, json={"username": self.username, "password": self.password})
        logger.info(f"Response: {response.json()}")
        return response.json()["access_token"]

    def get_dags(self):
        url = f"{self.airflow_baseurl}/api/v1/dags"
        logger.info(f"URL: {url}")
        response = self.session.get(url, **self.request_kwargs)
        logger.info(f"Response: {response.json()}")
        return response.json()
    
    def run_dag(self, dag_id: str, params: dict):
        url = f"{self.airflow_baseurl}/api/v1/dags/{dag_id}/dagRuns"
        conf = {"conf": params}
        response = self.session.post(url, **self.request_kwargs, json=conf)
        logger.info(f"Response: {response.text}")
        response_json = response.json()
        return response_json['dag_run_id'], response_json['state']
    
    @classmethod
    def __get_short_run(cls, airflow_run: dict):
        return {
            'run_id': airflow_run['dag_run_id'],
            'workflow_id': airflow_run['dag_id'],
            'status': airflow_run['state'],
            'start_time': airflow_run['start_date']
        }

    def get_runs(self, dag_id: str):
        url = f"{self.airflow_baseurl}/api/v1/dags/{dag_id}/dagRuns"
        response = self.session.get(url, **self.request_kwargs)
        logger.info(f"Response: {response.json()}")
        runs = response.json()['dag_runs']
        runs_list = [self.__get_short_run(run) for run in runs]
        return runs_list

    

    #def get_dag_runs(self, dag_id):
    #    return self.airflow_client.get_dag_runs(dag_id)
    
    
