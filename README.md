# Installation Guide

INCOMPLETE GUIDE!!

## Install podman

Install podman in rootless mode: [Podman Rootless](https://github.com/containers/podman/blob/main/docs/tutorials/rootless_tutorial.md).

add `unqualified-search-registries = ["registry.fedoraproject.org"]` to `/etc/containers/registries.conf`

Enable podman system service (user):
```
systemctl --user start podman.service
systemctl --user enable podman.service
```

## Issues

- look at (Qualified Namespaces)[https://github.com/containers/image/blob/main/docs/containers-registries.conf.5.md#note-risk-of-using-unqualified-image-names]



gunicorn --bind localhost:9000 wsgi:app
elm-live src/Main.elm --start-page=src/scanner.html --port=9001 -- --output=elm.js
