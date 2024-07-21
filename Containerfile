FROM registry.redhat.io/ubi9/ubi-minimal
RUN microdnf install python pip -y
RUN pip install fastapi uvicorn

COPY webhook.py /opt/webhook.py
CMD python /opt/webhook.py
