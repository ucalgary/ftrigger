FROM python:3.6.1-alpine

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY setup.py /usr/src/app
COPY finvoker /usr/src/app/finvoker
ARG SETUP_COMMAND=install
RUN apk add --no-cache --virtual .build-deps \
        gcc \
        git \
        musl-dev && \
    python setup.py ${SETUP_COMMAND} && \
    apk del .build-deps

LABEL maintainer="King Chung Huang <kchuang@ucalgary.ca>" \
      org.label-schema.vcs-url="https://git.ucalgary.ca/rms/functions/finvoker"
