FROM python:3.11

ENV PYTHONPATH $PYTHONPATH:/workdir
WORKDIR /workdir

RUN apt-get update &&\
    apt-get install -y --no-install-recommends \
    libsm6 libxext6 libgl1-mesa-glx &&\
    apt-get clean &&\
    rm -rf /var/lib/apt/lists/*

COPY ./ ./
RUN pip3 install --no-cache-dir -e .[tests,docs,examples]
