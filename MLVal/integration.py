import requests
from pathlib import Path 

storage_api_url = "http://192.168.1.35:7111"
db_api_url = "http://192.168.1.35:5055"

def get_val_paths(client_id, project_id, stand_id):
    body = {
        "entry": {
            "CLIENT_ID": client_id,
            "PROJECT_ID": project_id,
            "STAND_ID": stand_id
        },
        "filetype": "validation_data_and_boundary"
    }
    req = requests.post(storage_api_url + "/filepath", json=body)
    if not req.status_code == 200:
        raise ValueError("API call failed: " + str(req.text))
    return req.json()

def get_prediction_path(client_id, project_id, stand_id):
    body = {"client_id": client_id, "project_id": project_id, 
            "stand_id": stand_id}
    req = requests.post(db_api_url + "/api/stand_from_ids", json=body)
    if not req.status_code == 200:
        raise ValueError("API call failed: " + str(req.text))
    return req.json()[0]

if __name__ == "__main__":
    import sys
    cid, pid, sid = sys.argv[1:4]
    print(get_prediction_path(cid, pid, sid))
