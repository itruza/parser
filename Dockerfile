FROM python:latest
MAINTAINER Vadim Kalnin 'kalan4ikiii@gmail.com'

RUN apt update -y && apt install python3 python3-pip build-essential libssl-dev libffi-dev python3-dev nano net-tools chromium-driver -y

COPY ./parser /srv/www/parser
WORKDIR /srv/www/parser

RUN pip install -r Requirements.txt
