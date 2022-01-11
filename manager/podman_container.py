import os

from podman import PodmanClient
from podman.errors import PodmanError, BuildError, NotFound, APIError


CHROME_IMAGE_TAG = "chrome_scan"
PODMAN_SOCKET_URI = "unix:///run/user/1000/podman/podman.sock"
VNC_PORT = 5900
DEVTOOLS_PORT = 9222

# libpod rootless service unix domain socket (see
# https://docs.podman.io/en/latest/markdown/podman-system-service.1.html)
podman_client = PodmanClient(base_url=PODMAN_SOCKET_URI, version="2.0")


class Container:
    def __init__(self, container_id, name, labels, vnc_port, devtools_port):
        self.id = container_id
        self.name = name
        self.labels = labels
        self.vnc_port = vnc_port
        self.devtools_port = devtools_port

def stop_container(container_id):
    try:
        container = podman_client.containers.get(container_id)
    except NotFound as e:
        raise PodmanError(e)

    if container.status == "running":
        container.stop(timeout=3)
    container = podman_client.containers.get(container_id)
    container.remove(force=True)
    return


def build_container_image():
    os.chdir("chrome_container")
    try:
        image, logs = podman_client.images.build(
            path=".", dockerfile="Dockerfile", nocache=False, tag=CHROME_IMAGE_TAG
        )
        return {"image": str(image), "logs": logs}
    except BuildError as e:
        raise e
    finally:
        os.chdir("..")


def run_container():
    if not podman_client.images.exists(CHROME_IMAGE_TAG):
        raise PodmanError("Chrome Image does not exist.")
    port_mapping = {
        (str(VNC_PORT) + "/tcp"): None,
        (str(DEVTOOLS_PORT) + "/tcp"): None,
    }
    container = podman_client.containers.run(
        image=CHROME_IMAGE_TAG,
        ports=port_mapping,
        detach=True
    )

    if container.status != "running":
        raise PodmanError('Container is not running.')

    ports = get_host_ports(container)
    if VNC_PORT not in ports or DEVTOOLS_PORT not in ports:
        response_body = {
            "error": "Container port Mapping not correct.",
            "status": container.status
        }
        raise PodmanError("Container port mapping invalid. (status=%s" % container.status)

    return Container(container.id, container.name, container.labels, ports[VNC_PORT], ports[DEVTOOLS_PORT])


def get_host_ports(container):
    ports = dict()
    for port, port_info in container.ports.items():
        port = int(port[:-len("/tcp")])
        ports[port] = int(port_info[0]["HostPort"])
    return ports


def podman_available():
    try:
        podman_client.ping()
        return True
    except APIError as e:
        print('Error' + str(e))
        return False
