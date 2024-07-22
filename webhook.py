from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import json
import os
import base64

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
    uid: str
    allowed: bool
    patchType: str
    patch: str

class AdmissionReview(BaseModel):
    apiVersion: str
    kind: str
    response: AdmissionReviewResponse

def ensure_path(patch, base_path, keys):
    for i, key in enumerate(keys):
        path = f"{base_path}/{'/'.join(keys[:i+1])}"
        patch.append({
            "op": "add",
            "path": path,
            "value": {}
        })

@app.post("/mutate")
async def mutate_pod(admission_review: AdmissionReviewRequest):
    pod = Pod(**admission_review.request["object"])

    patches = []

    # Modify the CPU requests to 0.001 for all containers
    for i, container in enumerate(pod.spec.containers):
        base_path = f"/spec/containers/{i}/resources"
        if "requests" not in container.resources:
            ensure_path(patches, base_path, ["requests"])
        patches.append({
            "op": "add" if "cpu" not in container.resources.get("requests", {}) else "replace",
            "path": f"/spec/containers/{i}/resources/requests/cpu",
            "value": "0.001"
        })

    # Modify the CPU requests to 0.001 for all initContainers
    for i, container in enumerate(pod.spec.initContainers):
        base_path = f"/spec/initContainers/{i}/resources"
        if "requests" not in container.resources:
            ensure_path(patches, base_path, ["requests"])
        patches.append({
            "op": "add" if "cpu" not in container.resources.get("requests", {}) else "replace",
            "path": f"/spec/initContainers/{i}/resources/requests/cpu",
            "value": "0.001"
        })

    # Base64 encode the patch
    patch_str = json.dumps(patches)
    patch_bytes = patch_str.encode('utf-8')
    patch_base64 = base64.b64encode(patch_bytes).decode('utf-8')

    # Construct the response
    response = AdmissionReviewResponse(
        uid=admission_review.request["uid"],
        allowed=True,
        patchType="JSONPatch",
        patch=patch_base64
    )

    admission_review_response = AdmissionReview(
        apiVersion="admission.k8s.io/v1",
        kind="AdmissionReview",
        response=response
    )

    return admission_review_response

if __name__ == "__main__":
    cert_file = os.getenv("TLS_CERT_FILE")
    key_file = os.getenv("TLS_KEY_FILE")

    if not cert_file or not key_file:
        raise ValueError("TLS_CERT_FILE and TLS_KEY_FILE environment variables must be set")

    uvicorn.run(app, host="0.0.0.0", port=8000, ssl_keyfile=key_file, ssl_certfile=cert_file)
