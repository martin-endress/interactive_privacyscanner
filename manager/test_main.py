import json
import requests

manager_url = "http://localhost:5000/"

print('enter URL')
url = input()

response = requests.post(manager_url + "start_instance", json={"url": url}).json()
vnc_port = response['vnc_port']
container_id = response['container_id']
print('Container started. VNC PORT: %s' % vnc_port)

print('Press any key to start scan.')
input()

response = requests.post(manager_url + "start_scan", json={"container_id": container_id}).json()
print(json.dumps(response))

while True:
    print("Press any key to register interaction. 'Q' to quit.")
    action = input()
    if action == "Q":
        break
    response = requests.post(manager_url + "register_interaction", json={"container_id": container_id}).json()
    print(json.dumps(response))

response = requests.post(manager_url + "stop_scan", json={"container_id": container_id}).json()
print(json.dumps(response))
