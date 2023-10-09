FROM python:3.11-buster as app
MAINTAINER datapunt@amsterdam.nl

ENV PYTHONUNBUFFERED 1 \
    PIP_NO_CACHE_DIR=off

RUN apt-get update \
    && apt-get dist-upgrade -y \
    && apt-get install --no-install-recommends -y \
	&& apt-get install -y gdal-bin libgeos-dev netcat \
    && pip install --upgrade pip \
    && pip install uwsgi \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN adduser --system datapunt

RUN mkdir -p /src && chown datapunt /src
RUN mkdir -p /deploy && chown datapunt /deploy
RUN mkdir -p /var/log/uwsgi && chown datapunt /var/log/uwsgi

WORKDIR /install
ADD requirements.txt .
RUN pip install -r requirements.txt
RUN chmod -R a+r /install

WORKDIR /src

COPY src .
COPY deploy /deploy

USER datapunt

CMD ["/deploy/docker-run.sh"]

# devserver
FROM app as dev

USER root
WORKDIR /install
ADD requirements_dev.txt .
RUN pip install -r requirements_dev.txt

WORKDIR /src
USER datapunt

# Any process that requires to write in the home dir
# we write to /tmp since we have no home dir
ENV HOME /tmp

CMD ["python manage.py runserver 0.0.0.0"]

# tests
FROM dev as tests

USER datapunt
WORKDIR /tests
ADD tests .
COPY pyproject.toml /.

# ENV COVERAGE_FILE=/tmp/.coverage
ENV PYTHONPATH=/src
# ENV USE_JWKS_TEST_KEY=True

CMD ["pytest"]
