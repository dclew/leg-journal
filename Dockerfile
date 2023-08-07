FROM python:3.9-slim

RUN adduser journal

WORKDIR /home/trade-journal

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn pymysql cryptography

COPY app app
COPY migrations migrations
COPY main.py config.py boot.sh ./
RUN chmod +x boot.sh

ENV FLASK_APP main.py

RUN chown -R journal:journal ./
USER journal

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]