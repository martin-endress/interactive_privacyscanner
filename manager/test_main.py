import asyncio

import requests
from playwright.async_api import async_playwright,TimeoutError

import result


def main2():
    manager_url = "http://scanner.psi.test/api/"

    url = "http://www.example.com/"

    response = requests.post(manager_url + "replay_scan", json={"result_id": "heise.de_22-05-25_16-05"})
    print(response)
    vnc_port = response.json()['vnc_port']
    # container_id = response['container_id']
    print(f'Container started. vnc port: {vnc_port}')


selectors = [
     #notice > div:nth-child(2) > div > button
    '#notice > div:nth-child(2) > div > button',
    'xpath=/html/body/div/div[2]/div[2]/div/button',
    'button:has-text("Zustimmen")',
    'html > body > div > #notice > div:nth-child(2) > div > button'
]


async def main():
    async with async_playwright() as playwright:
        chromium = playwright.chromium
        browser = await chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto('http://heise.de/')
        await page.wait_for_load_state('networkidle')
        success = False
        while not success:
            for s in selectors:
                try:
                    await page.click(s, force=True, timeout=1000)  # 1 s timeout
                    print(f'Click successful using selector {s}.')
                    success = True
                    break
                except TimeoutError as e:
                    print(e)

        await browser.close()

def test():
    print(result.get_all_scans())

if __name__ == "__main__":
    test()
