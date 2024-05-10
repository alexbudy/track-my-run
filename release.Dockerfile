FROM python:3.11

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN apt-get update && apt-get -y install libpq-dev gcc

RUN pip install -r requirements.txt

COPY . /app

EXPOSE 80

ENTRYPOINT [ "python" ]

CMD ["server.py" ]