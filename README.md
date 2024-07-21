# Mutating webhook for admission controller that set the cpu requests to 0.001

Read the blog post here to understand why -> link

If for some reasons this work is usefull for you, don't use my container. Who knows what's inside!
Instead, build your own. See below for instructions

## Install python dependencies to run locally

```bash
pip install fastapi uvicorn
```

## Run locally with:
```bash
python webhook.py
```

This will start a server on 0.0.0.0:8000

## Test localy

### A pod with one container

```bash
curl -X POST -H "Content-Type: application/json" -d   @AdmissionReviewExamples/container.json http://localhost:8000/mutate | jq .
```
The output should looks something like:

```json
{
  "apiVersion": "admission.k8s.io/v1",
  "kind": "AdmissionReview",
  "response": {
    "uid": "0df28fbd-5f5f-11e8-bc74-36e6bb280816",
    "allowed": true,
    "patchType": "JSONPatch",
    "patch": [
      {
        "op": "add",
        "path": "/spec/containers/0/resources/requests",
        "value": {
          "cpu": "0.001"
        }
      }
    ]
  }
}

```

### A pod with two containers
```bash
curl -X POST -H "Content-Type: application/json" -d   @AdmissionReviewExamples/containers.json http://localhost:8000/mutate | jq .
```

### A pod with one container and one initContainer
```bash
curl -X POST -H "Content-Type: application/json" -d   @AdmissionReviewExamples/container_initContainer.json http://localhost:8000/mutate | jq .
```




## Build the container

The Containerfile is leveraging the Red Hat UBI-minimal base image. It's secured, slim, and will work on OpenShift out of the box. You may need to register for a Red Hat account, or you main need to use a different base image, and update it to meet OpenShift security requirements. Read this https://docs.openshift.com/container-platform/4.16/openshift_images/create-images.html#use-uid_create-images or this (it's an old post, but still valide) https://developers.redhat.com/blog/2020/10/26/adapting-docker-and-kubernetes-containers-to-run-on-red-hat-openshift-container-platform#

```bash
podman build . -t your_image_name
podman push your_image_name
```

## Deploy on your OpenShift cluster

