FROM ghcr.io/osai-ai/dokai:21.07-pytorch

# Examples requirements
COPY ./examples/requirements.txt /examples_requirements.txt
RUN pip3 install --no-cache-dir -r /examples_requirements.txt

# Tests requirements
COPY ./tests/requirements.txt /tests_requirements.txt
RUN pip3 install --no-cache-dir -r /tests_requirements.txt

# Docs requirements
COPY ./docs/requirements.txt /docs_requirements.txt
RUN pip3 install --no-cache-dir -r /docs_requirements.txt

ENV PYTHONPATH $PYTHONPATH:/workdir
WORKDIR /workdir
