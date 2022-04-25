import json
import logging

from flask import Flask, Response, request
from podman.errors import PodmanError
import time
import logs
from urllib.parse import urlparse
from interactive_scanner import InteractiveScanner
from podman_container import run_container, podman_available, stop_container
from scanner_messages import ScannerMessage, MessageType

# Init logging
logs.configure('scan_manager.log')
logger = logging.getLogger('manager')

# Init set of scanners (dict access is thread-safe https://docs.python.org/3/glossary.html#term-global-interpreter-lock)
scanners = dict()

# Init flask app
app = Flask(__name__)


@app.before_request
def before_request():
    if not podman_available():
        logger.error('Podman not available. No action was performed.')
        response_body = "Please start the podman service ('podman system service -t 0 &') or enable systemd user unit podman.service"
        return Response(response_body, status=500, mimetype="text/plain")
    # continue with request
    return None


@app.route('/start_scan', methods=['POST'])
def start_scan():
    """
    Starts an interactive scan.

    Starts a scanning instance which includes the container and a chrome manager subprocess.
    The subprocess is instructed through a message queue.
    The initial scan is executed.
    """
    # Fail fast
    if request.json == None:
        return Response("Request must be a json containing the URL.", status=400)
    url = request.json['url']
    try:
        urlparse(url)
    except ValueError as e:
        msg = str(e)
        logger.error(msg)
        return Response(msg, status=400)

    # Start container
    try:
        container = run_container()
    except PodmanError as e:
        msg = str(e)
        logger.error(msg)
        return Response(msg, status=503)

    # Start scanner thread
    scanner = InteractiveScanner(url, container.devtools_port, None)
    scanners[container.id] = scanner
    scanner.start()

    # Start initial scan
    scanner.put_msg(ScannerMessage(MessageType.StartScan, content=''))

    # Respond
    response_body = json.dumps(
        {"vnc_port": container.vnc_port, "container_id": container.id})
    return Response(response_body, status=200)


@app.route('/register_interaction', methods=['POST'])
def register_interaction():
    logging.info('registering interaction')
    try:
        scanner = get_scanner()
    except ValueError as e:
        return Response('Client Error: %s' % str(e), status=400)
    scanner.put_msg(ScannerMessage(
        MessageType.RegisterInteraction, content=''))
    return Response(status=200)


@app.route('/stop_scan', methods=['POST'])
def stop_scan():
    try:
        scanner = get_scanner()
        scanner.put_msg(ScannerMessage(
            MessageType.StopScan, content=container_id))
        return Response('Scan completion initiated.', status=200)
    except PodmanError as e:
        return Response('Server Error: %s' % str(e), status=500)
    except ValueError as e:
        return Response('Client Error: %s' % str(e), status=400)


@sock.route('/addSocket')
def addSocketConnection(socket):
    try:
        scanner = get_scanner()
        scanner.set_socket(socket)
        return  # close receiving side
    except ValueError as e:
        return Response('Client Error: %s' % str(e), status=400)


@app.route('/status', methods=['GET'])
def status():
    for s in scanners:
        s.send_socket_msg('asdf')
    return Response("server up", status=200)


@app.route('/stop_all_scans', methods=['POST'])
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


def get_scanner():
    request_body = request.get_json()
    container_id = request_body["container_id"]
    if container_id in scanners:
        return scanners[container_id]
    else:
        raise ValueError("Container with id %d does not exist." % container_id)
