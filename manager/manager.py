import json
import logging
from urllib.parse import urlparse

from flask import Flask, Response, request
from flask_sock import Sock
from podman.errors import PodmanError

import logs
import result
import scanner_messages
from errors import ScannerError
from interactive_scanner import InteractiveScanner
from podman_container import run_container, podman_available, stop_container
from result import ResultKey
from scanner_messages import ScannerMessage, MessageType

# Init logging
logs.configure('scan_manager.log')
logger = logs.get_logger('manager')

# Init set of scanners (dict access is thread-safe https://docs.python.org/3/glossary.html#term-global-interpreter-lock)
scanners = dict()

# Init flask app
app = Flask(__name__)

sock = Sock(app)


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
    logger.debug('start_scan')
    # Fail fast
    if request.json is None:
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
    scanner = InteractiveScanner(url, container.devtools_port, container.id, None)
    scanners[container.id] = scanner
    scanner.start()

    # Start initial scan
    scanner.put_msg(ScannerMessage(MessageType.StartScan))

    # Respond
    response_body = json.dumps(
        {"vnc_port": container.vnc_port, "container_id": container.id})
    return Response(response_body, status=200)


@app.route('/register_interaction', methods=['POST'])
def register_interaction():
    logging.debug('/register_interaction')
    try:
        scanner = get_scanner()
    except ValueError as e:
        return Response('Client Error: %s' % str(e), status=400)
    scanner.put_msg(ScannerMessage(MessageType.RegisterInteraction))
    return Response(status=200)


@app.route('/stop_scan', methods=['POST'])
def stop_scan():
    logging.debug('/stop_scan')
    try:
        scanner = get_scanner()
        scanner.put_msg(ScannerMessage(MessageType.StopScan))
        return Response('Scan completion initiated.', status=200)
    except PodmanError as e:
        return Response('Server Error: %s' % str(e), status=500)
    except ValueError as e:
        return Response('Client Error: %s' % str(e), status=400)


@app.route('/clear_cookies', methods=['POST'])
def clear_cookies():
    try:
        scanner = get_scanner()
        scanner.put_msg(ScannerMessage(MessageType.ClearCookies))
        return Response('Cookies deleted.', status=200)
    except PodmanError as e:
        return Response('Server Error: %s' % str(e), status=500)
    except ValueError as e:
        return Response('Client Error: %s' % str(e), status=400)


@app.route('/take_screenshot', methods=['POST'])
def take_screenshot():
    try:
        scanner = get_scanner()
        scanner.put_msg(ScannerMessage(MessageType.TakeScreenshot))
        return Response('Screenshot saved.', status=200)
    except PodmanError as e:
        return Response('Server Error: %s' % str(e), status=500)
    except ValueError as e:
        return Response('Client Error: %s' % str(e), status=400)


@sock.route('/addSocket')
def addSocket(socket):
    logger.info("Socket added. Waiting for container id.")
    while True:
        container_id = socket.receive()
        if container_id in scanners:
            scanners[container_id].set_socket(socket)
            logger.info("Scanner updated successfully.")


@app.route('/status', methods=['GET'])
def status():
    for s in scanners:
        s.send_socket_msg('asdf')
    return Response("server up", status=200)


@app.route('/stop_all_scans', methods=['POST'])
def stop_all_scans():
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


@app.route('/get_all_scans', methods=['GET'])
def get_all_scans():
    pass # todo


@app.route('/replay_scan', methods=['POST'])
def replay_scan():
    # Get Scan Info
    if request.json is None:
        return Response('Client Error: Request must be a JSON', status=400)
    result_id = request.json['result_id']
    try:
        scan_info = result.get_scan_info(result_id)
    except ScannerError as e:
        return Response(f'Client Error, result not found: {e}')

    # Start container
    try:
        container = run_container()
    except PodmanError as e:
        msg = str(e)
        logger.error(msg)
        return Response(msg, status=503)

    scanner = InteractiveScanner(scan_info[ResultKey.SITE_URL],
                                 container.devtools_port,
                                 container.id, None,
                                 reference_scan_id=result_id)
    scanners[container.id] = scanner
    scanner.start()

    # Define sequence
    for m in scanner_message_sequence(scan_info[ResultKey.INTERACTION]):
        scanner.put_msg(m)

    # Respond
    response_body = json.dumps({"vnc_port": container.vnc_port})
    return Response(response_body, status=200)


def scanner_message_sequence(interaction):
    message_sequence = []
    for i in interaction:
        # perform user interaction
        for user_interaction in i[ResultKey.USER_INTERACTION]:
            scan_msg = ScannerMessage(MessageType.PerformUserInteraction, content=user_interaction)
            message_sequence.append(scan_msg)

        # register event / stop scan
        scan_msg = scanner_messages.from_result_key(i[ResultKey.EVENT])
        message_sequence.append(scan_msg)
    return message_sequence


def get_scanner():
    if request.json is None:
        raise ValueError("Request must be JSON containing the container id.")
    container_id = request.json["container_id"]
    if container_id in scanners:
        return scanners[container_id]
    else:
        raise ValueError("Container with id %d does not exist." % container_id)
