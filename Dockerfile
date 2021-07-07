FROM python:3.7

WORKDIR /app

RUN pip install -U pip setuptools

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN rasa train
EXPOSE 5005
EXPOSE 5055
CMD rasa run&rasa run actions