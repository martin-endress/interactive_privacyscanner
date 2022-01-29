from celery import Celery
from interactive_scanner import InteractiveScanner

app = Celery('scanner_manager', backend='redis://localhost', broker='pyamqp://localhost')

scanners = dict()

@app.task
def add(x, y):
    return x + y


@app.task
def add_scanning_instance(url, dev_tools_port):
    scanner = InteractiveScanner(url, dev_tools_port, None)
    scanner.start()
    scanners[container.id] = scanner

