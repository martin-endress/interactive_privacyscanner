import json

from flask import Flask, Response, request

from interactive_scanner import InteractiveScanner
from podman_container import run_container, podman_available, stop_container
from scanner_messages import ScannerMessage, MessageType

# Init flask app
app = Flask(__name__)

# Init set of scanners
scanners = dict()


@app.before_request
def before_request():
    if not podman_available():
        response_body = json.dumps(
            {"error": "Please start the podman service. ('podman system service -t 0 &')"}
        )
        return Response(response_body, status=500, mimetype="application/json")


@app.route('/start_instance', methods=['POST'])
def start_instance():
    """
    Starts a scanning instance which includes the container and a chrome manager subprocess.
    The subprocess is instructed through a message queue.
    """
    url = request.json['url']

    # Start container
    container = run_container()

    # Start scanner thread
    scanner = InteractiveScanner(url, container.devtools_port, None)
    scanner.start()
    scanners[container.id] = scanner

    # Respond
    response_body = json.dumps({"vnc_port": container.vnc_port, "container_id": container.id})
    return Response(response_body, status=200)


@app.route('/start_scan', methods=['POST'])
def navigate_to_page():
    print('go to website')
    scanner = next(iter(scanners.values()))
    scanner.put_msg(ScannerMessage(MessageType.StartScan, content=''))



@app.route('/shutdown')
def shutdown():
    for c_id, scanner in scanners.items():
        stop_container(c_id)
        scanner.put_msg(ScannerMessage(MessageType.StopScan))
    return Response('good', status=200)
