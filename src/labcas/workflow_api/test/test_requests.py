import json
import requests

def json_pretty_print(data):
    pretty_json = json.dumps(data, indent=4)
    print(pretty_json)



LABCAS_WORKFLOW_SERVICE_URL = "http://localhost:5000"

def test_get_workflows():   
    response = requests.get(f"{LABCAS_WORKFLOW_SERVICE_URL}/workflows")
    json_pretty_print(response.json())
    assert response.status_code == 200
    assert response.json()[0]['id'] == "nebraska"
    assert response.json() is not None  

def test_run_workflow():
    workflow_id = "nebraska"
    params = {"in_bucket": "edrn-bucket", "in_prefix": "nebraska_images/", "out_bucket": "edrn-bucket" , "out_prefix": "nebraska_images_nuclei/"}
    payload = {"workflow_id": workflow_id, "params": params}
    response = requests.post(f"{LABCAS_WORKFLOW_SERVICE_URL}/runs", json=payload)
    json_pretty_print(response.json())
    assert response.status_code == 200
    assert response.json() is not None

def test_get_workflow_runs():
    workflow_id = "nebraska"
    response = requests.get(f"{LABCAS_WORKFLOW_SERVICE_URL}/workflows/{workflow_id}/runs")
    json_pretty_print(response.json())
    assert response.status_code == 200
    assert response.json() is not None



if __name__ == "__main__":
    #test_get_workflows()
    #test_run_workflow()
    test_get_workflow_runs()







