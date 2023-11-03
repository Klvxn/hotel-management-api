FROM python:3.10

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONPATH /src
ENV ENVIRONMENT production

WORKDIR /src

COPY ./requirements.txt /src

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . /src

RUN aerich init -t --tortoise-orm && \
    aerich init-db
