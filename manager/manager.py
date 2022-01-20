import json
import logging

from flask import Flask, Response, request
from podman.errors import PodmanError

import logs
from interactive_scanner import InteractiveScanner
from podman_container import run_container, podman_available, stop_container
from scanner_messages import ScannerMessage, MessageType

# Init logging
logs.configure('scan_manager.log')
logger = logging.getLogger('manager')

# Init set of scanners
scanners = dict()

# Init flask app
app = Flask(__name__)


@app.before_request
def before_request():
    if not podman_available():
        logger.error('Podman not available. No action was performed.')
        response_body = json.dumps(
            {"error": "Please start the podman service. ('podman system service -t 0 &')"}
        )
        return Response(response_body, status=500, mimetype="application/json")
    # continue with request
    return None


@app.route('/start_instance', methods=['POST'])
def start_instance():
    """
    Starts a scanning instance which includes the container and a chrome manager subprocess.
    The subprocess is instructed through a message queue.
    """
    url = request.json['url']

    # Start container
    try:
        container = run_container()
    except PodmanError as e:
        msg = str(e)
        logger.error(msg)
        return Response(json.dumps({"error": msg}), status=501)

    # Start scanner thread
    scanner = InteractiveScanner(url, container.devtools_port, None)
    scanner.start()
    scanners[container.id] = scanner

    # Respond
    response_body = json.dumps({"vnc_port": container.vnc_port, "container_id": container.id})
    return Response(response_body, status=200)


@app.route('/start_scan', methods=['POST'])
def navigate_to_page():
    logging.info('go to website')
    scanner = next(iter(scanners.values()))
    scanner.put_msg(ScannerMessage(MessageType.StartScan, content=''))


@app.route('/register_interaction', methods=['POST'])
def register_interaction():
    logging.info('registering interaction')
    try:
        scanner = scanners[get_container_id()]
    except ValueError as e:
        return Response('Client Error: %s' % str(e), status=400)
    scanner.put_msg(ScannerMessage(MessageType.RegisterInteraction, content=''))
    return Response(status=200)


@app.route('/stop_scan', methods=['POST'])
def stop_scan():
    try:
        container_id = get_container_id()
        stop_container(container_id=container_id)
        scanners[container_id].put_msg(ScannerMessage(MessageType.StopScan, content=''))
        return Response('Scan stopped.', status=200)
    except PodmanError as e:
        return Response('Server Error: %s' % str(e), status=500)
    except ValueError as e:
        return Response('Client Error: %s' % str(e), status=400)


@app.route('/stop_all_scans')
def shutdown():
    """
    Used for debugging purposes.
    """
    for c_id, scanner in scanners.items():
        try:
            stop_container(c_id)
            scanner.put_msg(ScannerMessage(MessageType.StopScan))
        except PodmanError as e:
            return Response('Server Error: %s' % str(e), status=500)
        except ValueError as e:
            return Response('Client Error: %s' % str(e), status=400)
    return Response('Shutdown successful.', status=200)


def get_container_id():
    request_body = request.get_json()
    container_id = int(request_body["container_id"])
    if container_id in scanners:
        return container_id
    else:
        raise ValueError("Container with id %d does not exist." % container_id)
