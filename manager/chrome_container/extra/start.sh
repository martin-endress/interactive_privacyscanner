#!/bin/bash

Xvfb :1 -screen 0 1280x900x16 & x11vnc -rfbauth /home/chrome/.vnc/passwd -forever -shared -bg -display :1.0 & DISPLAY=:1.0
