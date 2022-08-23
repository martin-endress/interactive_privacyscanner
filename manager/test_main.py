import asyncio
import csv
import json
from pathlib import Path
from urllib.parse import urlparse

from adblockeval import rules
from playwright.async_api import async_playwright, TimeoutError

import result
import utils

rule_files = ['resources/easylist.txt', 'resources/easyprivacy.txt', 'resources/fanboy-annoyance.txt']
rule_checker = rules.AdblockRules(rule_files=rule_files, skip_parsing_errors=True)


def generate_csv():
    with open(Path("/home/martin/git/interactive_privacyscanner/study/results.csv"), 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',')
        header = ['url',
                  'note',
                  'modal_present',
                  'banner_present',
                  # tp analysis
                  'additional_trackers',
                  'tp_cookies_after',
                  'tp_cookies_before',
                  'tp_requests_after',
                  'tp_requests_before',
                  'tracking_tp_after',
                  'tracking_tp_before',
                  # leak analysis before
                  'tp_id_leaks_before',
                  'tp_cookie_sync_before',
                  'fingerprinting_before',
                  # leak analysis after
                  'tp_id_leaks_after',
                  'tp_cookie_sync_after',
                  'fingerprinting_after',
                  ]

        csv_writer.writerow(header)

        results_path = Path("/home/martin/git/interactive_privacyscanner/study/data")
        i = 0
        for result_folder in results_path.iterdir():
            print(f'{i}) {result_folder.name}:')
            row = get_analysis(result_folder)
            csv_writer.writerow(row)
            i += 1


def get_analysis(result_path):
    row = list()
    # meta
    analysis_file = result_path / "first_scan" / "result.json"
    result_d = utils.load_json(analysis_file)
    if result_d:
        row.append(result_d['site url'])  # url

        user_note = ''
        if 'user_note' in result_d:
            user_note = result_d['user_note']
        row.append(user_note)  # note
        row.append(int(user_note.lower() == 'm'))  # modal_present
        row.append(int(user_note.lower() != 'x'))  # banner_present
    else:
        row += [-1] * 4

    # tp analysis
    analysis_file = result_path / "first_scan" / "analysis.json"
    analysis = utils.load_json(analysis_file)
    if analysis:
        row.append(analysis['additional_trackers'])  # additional_trackers
        row.append(analysis['tp_cookies_after'])  # tp_cookies_after
        row.append(analysis['tp_cookies_before'])  # tp_cookies_before
        row.append(analysis['tp_requests_after'])  # tp_requests_after
        row.append(analysis['tp_requests_before'])  # tp_requests_before
        row.append(analysis['tracking_tp_after'])  # tracking_tp_after
        row.append(analysis['tracking_tp_before'])  # tracking_tp_before
    else:
        row += [-1] * 7

    # cookie sync analysis before
    analysis_file = result_path / "first_scan" / "analysis_before" / "results.json"
    analysis = utils.load_json(analysis_file)
    if analysis:
        tp_id_leaks_before = sum(map(lambda c: len(c['associated3rdParties']), analysis['idLeaking']))
        row.append(tp_id_leaks_before)  # tp_id_leaks_before
        tp_cookie_sync_before = sum(map(lambda c: len(c['associated3rdParties']), analysis['cookieSync']))
        row.append(tp_cookie_sync_before)  # tp_cookie_sync_before
        fingerprinting_before = int(analysis['fingerprinting']['status'])
        row.append(fingerprinting_before)  # fingerprinting_before
    else:
        row += [-1] * 3

    # cookie sync analysis after
    analysis_file = result_path / "first_scan" / "analysis_after" / "results.json"
    analysis = utils.load_json(analysis_file)
    if analysis:
        tp_id_leaks_after = sum(map(lambda c: len(c['associated3rdParties']), analysis['idLeaking']))
        row.append(tp_id_leaks_after)  # tp_id_leaks_after
        tp_cookie_sync_after = sum(map(lambda c: len(c['associated3rdParties']), analysis['cookieSync']))
        row.append(tp_cookie_sync_after)  # tp_cookie_sync_after
        fingerprinting_after = int(analysis['fingerprinting']['status'])
        row.append(fingerprinting_after)  # fingerprinting_after
    else:
        row += [-1] * 3

    return row


def analyze():
    path = Path("/home/martin/git/interactive_privacyscanner/study/data")
    i = 0
    for result_folder in path.iterdir():
        if not result_folder.is_dir():
            print(f'{result_folder.name} skipped.')
            continue
        print(f'{i}) {result_folder.name}:')
        first_result_json_path = result_folder / result.FIRST_SCAN / result.RESULT_FILENAME
        with open(first_result_json_path) as f:
            r = json.load(f)

            scan_domain = str(urlparse(r[result.ResultKey.SITE_URL]).netloc)
            # cut off www
            if scan_domain.startswith('www.'):
                scan_domain = scan_domain[len('www.'):]

            interaction = r[result.ResultKey.INTERACTION]
            if len(interaction) != 2:
                print(f'{result_folder.name} skipped. (unexpected number of interactions: {len(interaction)})')
                continue
            analysis_filename = (result_folder / result.FIRST_SCAN)
            analyze_interaction(scan_domain, interaction[0], interaction[1], analysis_filename)
        i += 1


def contains_tracker(urls):
    return any(map(lambda x: x[1], urls))


def analyze_interaction(scan_domain, interaction_before, interaction_after, path):
    tp_cookies_before = get_third_parties_c(scan_domain, interaction_before['cookies'])
    tp_requests_before = get_third_parties_r(scan_domain, interaction_before['requests'])
    tracking_tp_before = {k for k, v in tp_requests_before.items() if contains_tracker(v)}
    tp_cookies_after = get_third_parties_c(scan_domain, interaction_after['cookies'])
    tp_requests_after = get_third_parties_r(scan_domain, interaction_after['requests'])
    tracking_tp_after = {k for k, v in tp_requests_after.items() if contains_tracker(v)}

    new_tp = tracking_tp_after - tracking_tp_before

    tp_analysis = {
        "tp_cookies_before": len(tp_cookies_before),
        "tp_requests_before": len(tp_requests_before),
        "tracking_tp_before": len(tracking_tp_before),
        "tp_cookies_after": len(tp_cookies_after),
        "tp_requests_after": len(tp_requests_after),
        "tracking_tp_after": len(tracking_tp_after),
        "additional_trackers": len(new_tp),
    }
    tp_analysis_detailed = {
        "tp_cookies_before": list(tp_cookies_before),
        "tp_cookies_after": list(tp_cookies_after),
        "tp_requests_before": list(tp_requests_before),
        "tracking_tp_before": list(tracking_tp_before),
        "tp_requests_after": list(tp_requests_after),
        "tracking_tp_after": list(tracking_tp_after),
        "additional_trackers": list(new_tp),
    }

    analysis_path = path / "analysis.json"
    utils.store_json(analysis_path, tp_analysis)

    analysis_path_detailed = path / "analysis_detailed.json"
    utils.store_json(analysis_path_detailed, tp_analysis_detailed)


def get_third_parties_c(first_party, cookies):
    cookies_parties = set()
    for c in cookies:
        domain = c['domain']
        if not domain.endswith(first_party) and rule_checker.match(domain, first_party).is_match:
            cookies_parties.add(domain)
    return cookies_parties


def get_third_parties_r(first_party, requests):
    requests_parties = dict()
    for r in requests:
        url = r['url']
        net_loc = str(urlparse(url).netloc)
        if not net_loc.endswith(first_party):
            if net_loc not in requests_parties:
                requests_parties[net_loc] = set()
            tracker = rule_checker.match(url[:150], r['document_url']).is_match
            requests_parties[net_loc].add((url, tracker))
    return requests_parties


# ------

selectors = [
    # generated through browser inspector (2)
    '#notice > div:nth-child(2) > div > button',
    'xpath=/html/body/div/div[2]/div[2]/div/button',
    # generated by playwright
    'button:has-text("Zustimmen")',
    # generated using simple css rule
    'html > body > div > #notice > div:nth-child(2) > div > button'
]


async def test_selectors():
    async with async_playwright() as playwright:
        chromium = playwright.chromium
        browser = await chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto('http://heise.de/')
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)
        for s in selectors:
            try:
                await page.click(s, force=True, timeout=500)  # 1 s timeout
                print(f'Click successful using selector {s}.')
                break
            except TimeoutError as e:
                print(e)
        print('waiting 30s')
        await asyncio.sleep(120)

        for s in selectors:
            try:
                await page.click(s, force=True, timeout=1000)  # 1 s timeout
                print(f'Click successful using selector {s}.')
                break
            except TimeoutError as e:
                print(e)

        await browser.close()


if __name__ == "__main__":
    generate_csv()
