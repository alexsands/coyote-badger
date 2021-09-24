FROM ubuntu:20.04

# Setup working directory
RUN mkdir -p /opt/coyotebadger
WORKDIR /opt/coyotebadger
ARG DEBIAN_FRONTEND=noninteractive

# Install microsoft/playwright additional dependencies
# See: https://github.com/microsoft/playwright/blob/master/utils/docker/Dockerfile.bionic
# Install WebKit dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libwoff1 \
    libopus0 \
    libwebp6 \
    libwebpdemux2 \
    libenchant1c2a \
    libgudev-1.0-0 \
    libsecret-1-0 \
    libhyphen0 \
    libgdk-pixbuf2.0-0 \
    libegl1 \
    libnotify4 \
    libxslt1.1 \
    libgles2 \
    libxcomposite1 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libepoxy0 \
    libgtk-3-0 \
    libharfbuzz-icu0
# Install gstreamer and plugins to support video playback in WebKit.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgstreamer-gl1.0-0 \
    libgstreamer-plugins-bad1.0-0 \
    gstreamer1.0-plugins-good \
    gstreamer1.0-libav
# Install Chromium dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-liberation \
    libnss3 \
    libxss1 \
    libasound2 \
    fonts-noto-color-emoji
# Install Firefox dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libdbus-glib-1-2 \
    libxt6
# Install XVFB to run browsers in headful mode
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb

# Install items for external/playwright-python
RUN apt-get update && apt-get install -y \
    git \
    curl \
    unzip

# Install python and pip
RUN apt-get update && apt-get install -y software-properties-common
RUN add-apt-repository -y ppa:deadsnakes/ppa
RUN apt-get update && apt-get install -y \
    python3.8 \
    python3-pip

# For debugging
RUN python3 --version
RUN pip3 --version

# Install package requirements from PyPI
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# Install external requirements from source
COPY external external
RUN pip3 install external/playwright-python-1.11.1

# For debugging
RUN pip3 freeze

# Install playwright browsers
RUN python3 -m playwright install

# Add source files
COPY coyote_badger coyote_badger
COPY docker.sh docker.sh

RUN chmod +x docker.sh
CMD ./docker.sh
