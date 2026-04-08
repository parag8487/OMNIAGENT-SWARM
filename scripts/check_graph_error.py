import os
import sys
import traceback

# Add backend directory to path
sys.path.append(os.path.abspath('backend'))

from app.services.graph_builder import GraphBuilderService
from app.config import Config

graph_id = "omniagent_ec2369f715c74ef6"
api_key = Config.ZEP_API_KEY

try:
    print(f"Testing graph_id: {graph_id}")
    print(f"Using Zep API Key: {api_key[:10]}...")
    builder = GraphBuilderService(api_key=api_key)
    data = builder.get_graph_data(graph_id)
    print("Success!")
    print(f"Result keys: {data.keys()}")
    if 'nodes' in data:
        print(f"Node count: {len(data['nodes'])}")
    if 'edges' in data:
        print(f"Edge count: {len(data['edges'])}")
except Exception as e:
    print(f"\n--- ERROR DETECTED ---")
    print(f"Type: {type(e).__name__}")
    print(f"Message: {e}")
    print("\nFull Traceback:")
    traceback.print_exc()
