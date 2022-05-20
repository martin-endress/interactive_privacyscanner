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


interaction = list()


async def main2():
    async with async_playwright() as playwright:
        chromium = playwright.chromium
        browser = await chromium.launch(headless=False)
        context = await browser.new_context()
        #await context.add_init_script(path="tmp/init.js")

        # create page
        page = await context.new_page()
        page.on("console", on_console)

        # navigate
        await page.goto("http://example.com")
        await page.add_script_tag(path="tmp/init.js")#, type='module')

        # end on input
        await asyncio.sleep(10000)

        # replay interaction
        context = await browser.new_context()
        # await context.add_init_script(path="tmp/init.js", type='module')
        page = await context.new_page()
        page.on("console", on_console)
        await page.goto("http://example.com")
        await page.add_script_tag(path="tmp/init.js", type='module')

        await asyncio.sleep(10)

        # for i in interaction:  #    print(f'Attempting to replay {i}.')  #    locator = page.locator(i)  #    for _ in range(5):  #        print('attempt')  #        print(await locator.count())  #        await asyncio.sleep(2)


#        await asyncio.sleep(3)


def on_console(console_message):
    scanner_key = 'SCANNER'
    if console_message.text.startswith(scanner_key):
        scanner_msg = console_message.text[len(scanner_key):]
        print(scanner_msg)
        interaction.append(scanner_msg)


if __name__ == "__main__":
    asyncio.run(main2())
