FROM python:3.9

# Tests requirements
COPY ./tests/requirements.txt /tests_requirements.txt
RUN pip3 install --no-cache-dir -r /tests_requirements.txt

ENV PYTHONPATH $PYTHONPATH:/workdir
WORKDIR /workdir
