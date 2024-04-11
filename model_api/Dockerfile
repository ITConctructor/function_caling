FROM ubuntu:jammy

RUN mkdir /app
RUN apt update && apt upgrade -y
RUN apt install -y python3 python3-pip curl netcat

ADD requirements.txt run.sh main.py /app

RUN python3 -m pip install -r /app/requirements.txt

CMD PYTHONPATH=/app /app/run.sh
