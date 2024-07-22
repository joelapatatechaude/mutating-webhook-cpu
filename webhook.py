from fastapi import FastAPI, Request
from pydantic import BaseModel
import uvicorn
import os

app = FastAPI()

class Container(BaseModel):
    name: str
    resources: dict = {}

class PodSpec(BaseModel):
    containers: list[Container]
    initContainers: list[Container] = []

class Pod(BaseModel):
    spec: PodSpec

class AdmissionReviewRequest(BaseModel):
    request: dict

class AdmissionReviewResponse(BaseModel):
    apiVersion: str
    kind: str
    response: dict

@app.post("/mutate")
async def mutate_pod(admission_review: AdmissionReviewRequest):
    pod = Pod(**admission_review.request["object"])

    patches = []

    # Function to add patch for a container
    def add_patch(container, index, container_type):
        if "requests" not in container.resources:
            patches.append({
                "op": "add",
                "path": f"/spec/{container_type}/{index}/resources/requests",
                "value": {"cpu": "0.001"}
            })
        else:
            patches.append({
                "op": "replace" if "cpu" in container.resources["requests"] else "add",
                "path": f"/spec/{container_type}/{index}/resources/requests/cpu",
                "value": "0.001"
            })

    # Modify the CPU requests to 0.001 for all containers
    for i, container in enumerate(pod.spec.containers):
        add_patch(container, i, "containers")

    # Modify the CPU requests to 0.001 for all initContainers
    for i, container in enumerate(pod.spec.initContainers):
        add_patch(container, i, "initContainers")

    # Construct the response
    response = {
        "uid": admission_review.request["uid"],
        "allowed": True,
        "patchType": "JSONPatch",
        "patch": patches
    }

    admission_review_response = {
        "apiVersion": "admission.k8s.io/v1",
        "kind": "AdmissionReview",
        "response": response
    }

    return AdmissionReviewResponse(**admission_review_response)

if __name__ == "__main__":
    cert_file = os.getenv("TLS_CERT_FILE")
    key_file = os.getenv("TLS_KEY_FILE")

    if not cert_file or not key_file:
        raise ValueError("TLS_CERT_FILE and TLS_KEY_FILE environment variables must be set")

    uvicorn.run(app, host="0.0.0.0", port=8000, ssl_keyfile=key_file, ssl_certfile=cert_file)
