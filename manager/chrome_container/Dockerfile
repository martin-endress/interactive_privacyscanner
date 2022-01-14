FROM fedora:latest

# Install packages
RUN dnf -y install chromium socat x11vnc xorg-x11-server-Xvfb
RUN dnf clean all

# Configure user
RUN useradd -m chrome
RUN echo "chrome:chrome" | chpasswd
RUN usermod -aG wheel chrome
USER chrome

# Copy service files
COPY extra/privacyscanner_browser.service /etc/systemd/system/privacyscanner_browser.service
COPY extra/privacyscanner_vnc.service /etc/systemd/system/privacyscanner_vnc.service
COPY extra/start.sh /home/chrome/start.sh

# Config chrome
RUN mkdir -p "/home/chrome/chrome-profile/Default"
COPY extra/Preferences /home/chrome/chrome-profile/Default/Preferences

# Config VNC
RUN mkdir "/home/chrome/.vnc"
RUN x11vnc -storepasswd "asdf" /home/chrome/.vnc/passwd

# Config VNC and logging
USER root
RUN chmod +x /home/chrome/start.sh
RUN mkdir -p /opt/privacyscanner/browser

# Enable services
RUN systemctl enable privacyscanner_browser
RUN systemctl enable privacyscanner_vnc

# Expose ports
EXPOSE 5900
EXPOSE 9222

# Init systemd container
CMD [ "/sbin/init" ]
