FROM python:3.12-slim

COPY lux2prom.py .
COPY requirements.txt .
RUN pip install -r requirements.txt
CMD ["python", "-u", "./lux2prom.py"] 
