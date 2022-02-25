FROM ubuntu:20.04

# Setup working directory
RUN mkdir -p /opt/coyotebadger
WORKDIR /opt/coyotebadger

# Setup env and args
ENV PYTHONUNBUFFERED=1
ARG DEBIAN_FRONTEND=noninteractive

# Install python and pip
RUN apt-get update && apt-get install -y \
    software-properties-common \
    git
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

# Install playwright browsers
RUN playwright install chromium firefox
RUN playwright install-deps chromium firefox

# Install XFCE4 and TigerVNC to run browsers in headful mode
RUN apt-get update && apt-get install -y \
    xfce4 \
    xfce4-goodies \
    wmctrl \
    xterm
RUN apt-get purge -y \
    pm-utils \
    xfce4-panel \
    xscreensaver*
RUN apt-get update && apt-get install -y \
    tigervnc-standalone-server \
    tigervnc-common
RUN mkdir ~/.vnc
RUN echo "password" | vncpasswd -f >> ~/.vnc/passwd
RUN chmod 600 ~/.vnc/passwd
ADD xfce4/xstartup /root/.vnc/xstartup
RUN chmod +x ~/.vnc/xstartup
ADD xfce4/xfce4-desktop.xml /root/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-desktop.xml
ADD xfce4/xfce4-power-manager.xml /root/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-power-manager.xml

# Install and setup noVNC to view VNC client
RUN git clone --branch=v1.1.0 https://github.com/novnc/noVNC.git
ENV XFCE_PANEL_MIGRATE_DEFAULT 1
ADD xfce4/noVNC.html noVNC/index.html

# For debugging
RUN pip3 freeze

# Add source files
COPY coyote_badger coyote_badger
COPY xfce4 xfce4
COPY docker.sh docker.sh

# Run the boot up script
RUN chmod +x docker.sh
CMD ./docker.sh
