import requests
import time
import json
import os

BASE_URL = "http://localhost:5001/api"
PROJECT_ID = None
GRAPH_ID = None
SIMULATION_ID = None

def test_flow():
    # 1. Upload file and create project
    print("Step 1: Creating project...")
    files = {'files': open(r'c:\Users\ASUS\Desktop\GEN\test_data.txt', 'rb')}
    data = {
        "simulation_requirement": "Analyze the impact of autonomous agents on healthcare prediction.",
        "project_name": "E2E Verification Project"
    }
    resp = requests.post(f"{BASE_URL}/graph/ontology/generate", files=files, data=data)
    if resp.status_code != 200:
        print(f"Failed to create project: {resp.text}")
        return
    project_data = resp.json()['data']
    project_id = project_data['project_id']
    print(f"Project created: {project_id}")

    # No separate Task for ontology generation in this specific route (it is synchronous in graph.py)
    # The ontology is already in project_data
    ontology = project_data['ontology']
    print(f"Ontology generated: {len(ontology['entity_types'])} entity types")

    # 3. Build Graph
    print("Step 3: Building graph...")
    resp = requests.post(f"{BASE_URL}/graph/build", json={"project_id": project_id})
    if resp.status_code != 200:
        print(f"Failed to start graph build: {resp.text}")
        return
    task_id = resp.json()['data']['task_id']
    
    while True:
        resp = requests.get(f"{BASE_URL}/graph/task/{task_id}")
        status = resp.json()['data']['status']
        print(f"Ontology status: {status}")
        if status == 'completed':
            break
        elif status == 'failed':
            print(f"Ontology failed: {resp.json()}")
            return
        time.sleep(2)

    # 3. Build Graph
    print("Step 3: Building graph...")
    resp = requests.post(f"{BASE_URL}/graph/build", json={"project_id": project_id})
    if resp.status_code != 200:
        print(f"Failed to start graph build: {resp.text}")
        return
    task_id = resp.json()['data']['task_id']
    
    while True:
        resp = requests.get(f"{BASE_URL}/task/{task_id}")
        data = resp.json()['data']
        status = data['status']
        print(f"Graph build status: {status} | Progress: {data.get('progress')}%")
        if status == 'completed':
            graph_id = data['result']['graph_id']
            break
        elif status == 'failed':
            print(f"Graph build failed: {data}")
            return
        time.sleep(5)
    
    print(f"Graph built: {graph_id}")

    # 4. Check for personas
    print("Step 4: Checking for personas...")
    resp = requests.get(f"{BASE_URL}/simulation/entities/{graph_id}")
    if resp.status_code != 200:
        print(f"Failed to fetch entities: {resp.text}")
        return
    entities = resp.json()['data']['entities']
    print(f"Found {len(entities)} personas")
    
    if len(entities) == 0:
        print("CRITICAL: 0 personas found in new graph!")
        # Check Zep directly
        from zep_cloud.client import Zep
        ZEP_API_KEY = "z_1dWlkIjoiaG91c3RvbiIsImlhdCI6MTc0Mzk4MDM0MH0.A5-N839D37qD_6a2uByfshZtV-G9VstT6eF8Xy1S8n4"
        client = Zep(api_key=ZEP_API_KEY)
        try:
            nodes = client.graph.node.get_nodes(graph_id=graph_id, page_number=1, page_size=10)
            print(f"Zep Raw Check: {len(nodes)} nodes found")
            for node in nodes:
                print(f"Node: {node.name} | Labels: {node.labels}")
        except Exception as e:
            print(f"Zep Raw Error: {e}")
        return

    # 5. Create Simulation
    print("Step 5: Creating simulation...")
    resp = requests.post(f"{BASE_URL}/simulation/create", json={"project_id": project_id})
    simulation_id = resp.json()['data']['simulation_id']
    print(f"Simulation created: {simulation_id}")

    # 6. Prepare Simulation
    print("Step 6: Preparing simulation...")
    resp = requests.post(f"{BASE_URL}/simulation/prepare", json={"simulation_id": simulation_id})
    task_id = resp.json()['data'].get('task_id')
    if not task_id:
        print("Preparation already complete or failed immediately.")
        return

    while True:
        # Note: /prepare/status is a POST endpoint in the code
        resp = requests.post(f"{BASE_URL}/simulation/prepare/status", json={"task_id": task_id})
        data = resp.json()['data']
        status = data['status']
        print(f"Preparation status: {status} | Progress: {data.get('progress')}%")
        if status == 'completed' or status == 'ready':
            break
        elif status == 'failed':
            print(f"Preparation failed: {data}")
            return
        time.sleep(5)

    print("Success: Pipeline fully verified!")

if __name__ == "__main__":
    test_flow()
