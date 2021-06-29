FROM python:3.9

RUN apt-get update &&\
    apt-get install -y --no-install-recommends \
    libsm6 libxext6 libgl1-mesa-glx &&\
    apt-get clean &&\
    rm -rf /var/lib/apt/lists/*

# Tests requirements
COPY ./tests/requirements.txt /tests_requirements.txt
RUN pip3 install --no-cache-dir -r /tests_requirements.txt

# Examples requirements
COPY ./examples/requirements.txt /examples_requirements.txt
RUN pip3 install --no-cache-dir -r /examples_requirements.txt

ENV PYTHONPATH $PYTHONPATH:/workdir
WORKDIR /workdir
