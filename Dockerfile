FROM debian:buster
MAINTAINER Abhas Abhinav <abhas@deeproot.in>

RUN apt-get -y update
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y vim less wget curl git net-tools telnet tcpdump netcat-openbsd python3 python3-pip procps rabbitmq-server
ADD . /home/colossus/
WORKDIR /home/colossus/
RUN pip3 install -r requirements/development.txt
RUN python3 manage.py migrate
EXPOSE 8000
CMD python3 manage.py runserver 0.0.0.0:8000
