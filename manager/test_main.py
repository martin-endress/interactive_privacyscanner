import asyncio
import json
import time

import requests
from playwright.async_api import async_playwright


def main():
    manager_url = "http://scanner.psi.test/api/"

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


interaction_log = list()


async def main2():
    async with async_playwright() as playwright:
        chromium = playwright.chromium
        browser = await chromium.launch(headless=False)
        context = await browser.new_context()

        # create page
        page = await context.new_page()
        await page.add_init_script(path="tmp/init.js")
        page.on("console", on_console)

        # navigate
        await page.goto("http://example.com/")

        await asyncio.sleep(15)
        await browser.close()

        # replay interaction
        browser = await chromium.launch(headless=False)
        context = await browser.new_context()

        # create page
        page = await context.new_page()
        await page.add_init_script(path="tmp/init.js")

        # navigate
        await page.goto("http://example.com/")
        try:
            for interaction in interaction_log:
                await asyncio.sleep(3)
                selector = interaction['selector']
                print(f'Attempting to replay {selector} event.')
                locator = page.locator(selector)
                await locator.click()
        except TimeoutError as e:
            print('Unable to replay interaction, 30s timeout exceeded.')
        await asyncio.sleep(3)
        await browser.close()


def on_console(console_message):
    scanner_key = 'SCANNER_INTERACTION'
    print(console_message)
    if console_message.text.startswith(scanner_key):
        scanner_msg = console_message.text[len(scanner_key):]
        interaction_json = json.loads(scanner_msg)
        interaction_log.append(interaction_json)
        print(interaction_json)


if __name__ == "__main__":
    asyncio.run(main2())
