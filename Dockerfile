FROM python:3.7.8-slim-stretch

WORKDIR /uploader/
COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .

VOLUME ["/uploader/upload"]

ENTRYPOINT ["python", "main.py"]