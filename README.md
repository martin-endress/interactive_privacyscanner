# Interactive Privacyscanner

This repository contains the prototype implementation of the privacy scanner, which was developed as part of my master thesis titled 'Semi-automated Interactive Website Scanning for Comprehensive Privacy Analysis'.
The scanner is a web measurement tool that models user interaction with websites.
It is conceptualized as a research tool to study possibly unobserved tracking techniques on internal web pages.

Thesis Supervisor: [Prof. Dr. Dominik Herrmann](https://www.uni-bamberg.de/psi/team/dominik-herrmann/)  
Thesis Advisor: [Henning Pridöhl](https://www.uni-bamberg.de/psi/team/henning-pridoehl/)



## Build Requirements

Following dependencies must be installed to deploy this project:


### System Files

The user `scanner` is created (e.g. `adduser scanner`).
The repository is cloned to `/home/scanner`.

Custom systemd files are linked or placed in `/etc/systemd/system`:

```
ln -s /home/scanner/interactive_privacyscanner/system_files/privacyscanner_manager.service
ln -s /home/scanner/interactive_privacyscanner/system_files/interactive-privacyscanner.target
```



### Python

Python 3.10 or higher is required due to the use of pattern matching.

Further packages should be installed as a virtual env:

Install `requirements.txt` to virtual environment in `manager/`:
```
pip install virtualenv
virtualenv venv
source venv/local/bin/activate
pip install -r requirements.txt
```

### Podman

[Podman](https://podman.io/) is a container engine for managing OCI containers on linux machines.
It facilitates the execution and isolation of complex applications in containers using systemd and other Linux kernel APIs.

1. Install podman in [rootless mode](https://github.com/containers/podman/blob/main/docs/tutorials/rootless_tutorial.md):
    1. Install packages podman, slirp4netns, fuse-overlayfs .
    2. Ensure that `/proc/sys/user/max_user_namespaces` is a reasonable number (15000). Problems might occur on RHEL7 machines.
    3. Add a repository to `/etc/containers/registries.conf`, for example (notice the [risk of using unqualified image names](https://github.com/containers/image/blob/main/docs/containers-registries.conf.5.md#note-risk-of-using-unqualified-image-names)):
        ```
        unqualified-search-registries = ["registry.fedoraproject.org"]
        ```
    4. Assign `subuids` and `subgids` for user `scanner`:
        ```
        usermod --add-subuids 100000-165535 scanner
        usermod --add-subgids 100000-165535 scanner
        ```
2. Enable the podman systemd service as a user (!) service. This step is not required for using podman from the command line (CLI), but is required for programmatic access.
    ```
    systemctl --user start podman.socket
    systemctl --user enable podman.socket
    ```
3. Ensure that `podman.socket` is listening at `/run/user/$UID/podman/podman.sock`, with `$UID` > 1000. Adjust `manager.cfg` according to the socket listen address.
4. Build the Browser container.
    ```
    cd chrome_container/
    podman build -t chrome_scan .
    ```

### Elm

### Nginx

### Guacamole

### Python



## Development

elm-live src/Main.elm --start-page=src/scanner.html --port=9001 -- --output=elm.js
