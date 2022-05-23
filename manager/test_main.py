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

        # create page
        page = await context.new_page()
        await page.add_init_script(path="tmp/init.js")
        page.on("console", on_console)

        # navigate
        await page.goto("http://heise.de/")
        # await page.add_script_tag(path="tmp/init.js", type='module')

        await asyncio.sleep(2)
        l = page.locator('button:has-text("Zustimmen")')
        print(await l.count())

        await asyncio.sleep(1500)
        recording = False
        await browser.close()

        # replay interaction
        browser = await chromium.launch(headless=False)
        context = await browser.new_context()

        # create page
        page = await context.new_page()
        await page.add_init_script(path="tmp/init.js")

        # navigate
        await page.goto("http://heise.de/")

        for i in interaction:
            found = False
            print(f'Attempting to replay {i}.')
            locator = page.locator(i)
            await asyncio.sleep(5)
            attempts = 5
            for i in range(attempts):
                print(f'Attempt {i + 1} of {attempts}')
                num_locators = await locator.count()
                print(f'num locators: {num_locators}')
                if num_locators == 1:
                    print('locator found, clicking link')
                    await locator.click()
                    found = True
                    break
                await asyncio.sleep(5)
            if not found:
                print('error')
                break
        await asyncio.sleep(3)
        await browser.close()


#        await asyncio.sleep(3)


def on_console(console_message):
    scanner_key = 'SCANNER'
    if console_message.text.startswith(scanner_key):
        scanner_msg = console_message.text[len(scanner_key):]
        print(scanner_msg)
        interaction.append(scanner_msg)


if __name__ == "__main__":
    asyncio.run(main2())
