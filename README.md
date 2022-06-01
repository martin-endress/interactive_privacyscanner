# Interactive Privacyscanner

This repository contains the prototype implementation of the privacy scanner, which was developed as part of my master thesis titled 'Semi-automated Interactive Website Scanning for Comprehensive Privacy Analysis'.
The scanner is a web measurement tool that models user interaction with websites.
It is conceptualized as a research tool to study possibly unobserved tracking techniques on internal web pages.

Thesis Supervisor: [Prof. Dr. Dominik Herrmann](https://www.uni-bamberg.de/psi/team/dominik-herrmann/)  
Thesis Advisor: [Henning Pridöhl](https://www.uni-bamberg.de/psi/team/henning-pridoehl/)



## Build Requirements

Following dependencies must be installed to deploy this project:

### Repository and User

Create a sudo user `scanner` (e.g. `adduser scanner`).
Clone the repository to `/home/scanner` and link it from `/usr/lib`.

### Guacamole + Tomcat (Backend)

[Guacamole](https://guacamole.apache.org/) is a clientless remote desktop gateway.
It supports the protocols VNC, RDP, and SSH.

The guacamole backend `guacd` is independent from the guacamole application servlet.
Follow the instructions of [Installing Guacamole natively](https://guacamole.apache.org/doc/gug/installing-guacamole.html) for a VNC setup.

> Depending on your distribution, some package names might not match the guide exactly, may even be installed from source, or might require you to change source repositories.


> If Java 11 does not work, try Java 8.

After installation of guacamole and tomcat, deploy the servlet to tomcat.

```
scanner:~/interactive_privacyscanner/guacamole_backend$
mvn package
mv target/guacamole-backend-1.0.war /var/lib/tomcat8/webapps/
```

Start and enable the systemd units `guacd.service` and `tomcat.service`.

> The directory `/var/lib/tomcat8/webapps/ROOT` can be removed safely.

### Python (Backend)

Python 3.10 or higher is required due to the use of pattern matching.

Further packages should be installed as a virtual env:

Install `requirements.txt` to virtual environment in `manager/`:
```
pip install virtualenv
virtualenv venv
source venv/local/bin/activate
pip install -r requirements.txt
```

### Podman (Backend)

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

### Elm (Frontend)

[Elm](https://elm-lang.org/) is a functional language that compiles to JavaScript (and html).
It does without runtime exceptions, enforces understandable code, is fast and type safe.

1. Download and install elm as described [here](https://guide.elm-lang.org/install/elm.html).
2. Install `uglify-js`.
3. make frontend (`frontend/Makefile`).

### Nginx

Install nginx and enable the respective systemd unit.
The nginx config file is linked in `/etc/nginx/sites-enabled/`:

```
ln -s /home/scanner/interactive_privacyscanner/system_files/nginx/scanner
```

> The nginx configuration contains two server instances:
> `scanner.psi.live` serves the compiled frontend `target/scanner.html`, whereas `scanner.psi.test` proxies requests to a development server running separately, e.g., `elm-live`.
> See development section for details.

Add both entries to `/etc/hosts`:

```
127.0.0.1     scanner.psi.test
127.0.0.1     scanner.psi.live
```

Start and enable `nginx.service`.

### System Files

Following `/system_files` must be moved or linked to specific locations:

Systemd files must be linked in `/etc/systemd/system`:

```
ln -s /home/scanner/interactive_privacyscanner/system_files/privacyscanner_manager.service
ln -s /home/scanner/interactive_privacyscanner/system_files/interactive-privacyscanner.target
```

> Check `systemctl list-dependencies interactive-privacyscanner.target` to see if all services are running.

## Development

elm-live src/Main.elm --start-page=src/scanner.html --port=9001 -- --output=elm.js
