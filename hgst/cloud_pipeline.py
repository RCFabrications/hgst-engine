import json
from hgst.kinematics import TopologicalKinematicsEngine

def run_cloud_kinematics_pipeline(input_payload):
    """
    GCP Cloud Functions / Cloud Run entry point for GCS event-driven processing.
    Connects supple-kayak-466010-v7-pyrite-payload-store to HGST topological verification.
    """
    data = json.loads(input_payload) if isinstance(input_payload, str) else input_payload
    
    engine = TopologicalKinematicsEngine()
    
    if "ratios" in data:
        ratios = data.get("ratios", [1.0, 1.0, 1.0, 1.0])
        backlashes = data.get("backlashes", [0.0, 0.0, 0.0, 0.0])
        return engine.evaluate_drivetrain(ratios, backlashes)
    elif "boundary_segments" in data:
        return engine.validate_boundary_loop(data["boundary_segments"])
    else:
        return {"error": "Invalid schema: Expected 'ratios' or 'boundary_segments'"}
