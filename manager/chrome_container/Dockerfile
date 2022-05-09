FROM fedora:latest

# Add google chrome to packages
RUN dnf -y install fedora-workstation-repositories dnf-plugins-core
RUN dnf config-manager --set-enabled google-chrome

# Install packages
RUN dnf -y install google-chrome-stable socat x11vnc xorg-x11-server-Xvfb
RUN dnf clean all

# Configure user
RUN useradd -m chrome
RUN echo "chrome:chrome" | chpasswd
RUN usermod -aG wheel chrome
USER chrome

# Copy service files
COPY extra/privacyscanner_browser.service /etc/systemd/system/privacyscanner_browser.service
COPY extra/privacyscanner_vnc.service /etc/systemd/system/privacyscanner_vnc.service
COPY extra/privacyscanner_proxy.service /etc/systemd/system/privacyscanner_proxy.service
COPY extra/start.sh /home/chrome/start.sh

# Config chrome
RUN mkdir -p "/home/chrome/.config/chromium/Default"
COPY extra/Preferences /home/chrome/.config/google-chrome/Default/Preferences

# Config VNC
RUN mkdir "/home/chrome/.vnc"
RUN x11vnc -storepasswd "asdf" /home/chrome/.vnc/passwd

# Config VNC and logging
USER root
RUN chmod +x /home/chrome/start.sh
RUN mkdir -p /opt/privacyscanner/browser

# Fix ownership
RUN chown -R chrome:chrome /home/chrome/.config/google-chrome

# Enable services
RUN systemctl enable privacyscanner_browser
RUN systemctl enable privacyscanner_vnc
RUN systemctl enable privacyscanner_proxy

# Expose ports
EXPOSE 5900
EXPOSE 9000

# Init systemd container
CMD [ "/sbin/init" ]
