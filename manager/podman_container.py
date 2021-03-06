import os
from datetime import datetime

from podman import PodmanClient
from podman.errors import PodmanError, BuildError, NotFound, APIError

import config
import logs

CHROME_IMAGE_TAG = "chrome_scan"
VNC_PORT = 5900
DEVTOOLS_PORT = 9000

PODMAN_SOCKET_URI = "unix://" + config.podman['podman_socket']

# max lifetime in seconds (5 Minutes)
CONTAINER_MAX_LIFETIME = 60 * 5

logger = logs.get_logger('podman_api')

# libpod rootless service unix domain socket
# (see https://docs.podman.io/en/latest/markdown/podman-system-service.1.html)
podman_client = PodmanClient(base_url=PODMAN_SOCKET_URI, version="2.0")


class Container:
    def __init__(self, container_id, name, labels, vnc_port, devtools_port):
        self.id = container_id
        self.name = name
        self.labels = labels
        self.vnc_port = vnc_port
        self.devtools_port = devtools_port


def build_container_image():
    os.chdir("../chrome_container")
    logger.info("Building Container image.")
    try:
        image, logs = podman_client.images.build(
            path=".", dockerfile="Dockerfile", nocache=False, tag=CHROME_IMAGE_TAG
        )
        return {"image": str(image), "logs": logs}
    except BuildError as e:
        logger.error("Build failed, exiting.")
        raise PodmanError(e)
    finally:
        os.chdir("..")


def run_container():
    if not podman_client.images.exists(CHROME_IMAGE_TAG):
        raise PodmanError("Chrome image does not exist.")
    port_mapping = {
        (str(VNC_PORT) + "/tcp"): None,
        (str(DEVTOOLS_PORT) + "/tcp"): None,
    }
    container = podman_client.containers.run(
        image=CHROME_IMAGE_TAG,
        # ports (Dict[str, Union[int, Tuple[str, int], List[int]]]): Ports to bind inside the container.
        ports=port_mapping,
        # remove (bool): Remove the container when it has finished running. Default: False.
        remove=True,
        # detach (bool): Run container in the background and return a Container object.
        detach=True,
        # shm_size (Union[str, int]): Size of /dev/shm (e.g. 1G).
        shm_size=2 * 2 ** (10 * 3)  # 2gb, str does not work for some reason
    )

    if container.status != "running":
        raise PodmanError('Container is not running.')

    logger.info(f"Started new container instance. (container id={container.id})")
    ports = _get_host_ports(container)
    if VNC_PORT not in ports or DEVTOOLS_PORT not in ports:
        raise PodmanError(f"Container port mapping invalid. (status={container.status})")

    return Container(container.id, container.name, container.labels, ports[VNC_PORT], ports[DEVTOOLS_PORT])


def stop_container(container_id):
    try:
        container = podman_client.containers.get(container_id)
    except NotFound as e:
        raise PodmanError(e)

    if container.status == "running":
        container.stop(timeout=5)
    else:
        raise PodmanError('Container is not running.')


def podman_available():
    """
    Returns True if Podman service is running correctly.
    """
    try:
        return podman_client.ping()
    except APIError as e:
        logger.error(f'Error {e}')
        return False


def kill_old_containers():
    containers = podman_client.containers.list()
    for c in containers:
        started_at = c.inspect()['State']['StartedAt']
        # StartedAt does not conform to ISO date, but it has 8 instead of 6 microsecond digits
        # e.g. '2022-06-07T15:18:51.949951782+02:00'
        iso_started_at = started_at[:started_at.find('.')]
        run_time = datetime.now() - datetime.fromisoformat(iso_started_at)
        if run_time.seconds > CONTAINER_MAX_LIFETIME:
            logger.warn(f'Container {c.id} reached its max age (30 minutes) and was shut down.')
            c.stop()
            c.remove()


def _get_host_ports(container):
    ports = dict()
    for port, port_info in container.ports.items():
        port = int(port[:-len("/tcp")])
        ports[port] = int(port_info[0]["HostPort"])
    return ports
