FROM ubuntu:20.04

# Setup working directory
RUN mkdir -p /opt/coyotebadger
WORKDIR /opt/coyotebadger
ARG DEBIAN_FRONTEND=noninteractive

# Install XVFB to run browsers in headful mode
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb

# Install python and pip
RUN apt-get update && apt-get install -y software-properties-common
RUN add-apt-repository -y ppa:deadsnakes/ppa
RUN apt-get update && apt-get install -y \
    python3.9 \
    python3-pip

# For debugging
RUN python3 --version
RUN pip3 --version

# Install package requirements from PyPI
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# For debugging
RUN pip3 freeze

# Install playwright browsers
RUN playwright install
RUN playwright install-deps

# Add source files
COPY coyote_badger coyote_badger
COPY docker.sh docker.sh

RUN chmod +x docker.sh
CMD ./docker.sh
