FROM alpine:3.19

RUN apk add --no-cache bash curl jq python3 py3-pip \
    && ln -sf /usr/bin/python3 /usr/bin/python

WORKDIR /workspace

CMD ["bash", "/workspace/tests/run_tests.sh"]


