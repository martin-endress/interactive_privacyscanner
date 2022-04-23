# System Files

These files must be linked or copied to different system directories.

To check the target services, type:

```
systemctl list-dependencies interactive-privacyscanner.target
```

## Systemd service files

System files should reside in `/etc/systemd/system`.


## NGINX server config

the scanner server config is stored in /etc/nginx/sites-enabled

Move or link this file:

```
ln -s system_files/nginx/scanner /etc/nginx/sites-enabled
```

