import requests


def main():
    manager_url = "http://scanner.psi.test/api/"

    url = "http://www.example.com/"

    response = requests.post(manager_url + "replay_scan", json={"result_id": "heise.de_22-05-25_14-24"})
    print(response)
    vnc_port = response.json()['vnc_port']
    # container_id = response['container_id']
    print(f'Container started. vnc port: {vnc_port}')


if __name__ == "__main__":
    main()
