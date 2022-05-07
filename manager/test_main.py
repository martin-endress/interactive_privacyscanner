import requests

import time

def main():
    manager_url = "http://scanner.psi.test/api/"

    #url = input()
    url = "http://www.heise.de/"

    response = requests.post(manager_url + "start_scan", json={"url": url}).json()
    vnc_port = response['vnc_port']
    container_id = response['container_id']
    print('Container started. vnc port: %s, container id: %s' % (vnc_port, container_id))

    time.sleep(5)

    print('Sutting down container')
    
    response = requests.post(manager_url + "stop_scan", json={"container_id": container_id})
    if response.status_code != 200:
        print('error')
        print(response)


if __name__ == "__main__":
    main()
