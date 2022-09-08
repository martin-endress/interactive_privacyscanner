import asyncio
import csv
import json
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

from adblockeval import rules
from playwright.async_api import async_playwright, TimeoutError

import result
import utils

rule_files = ['resources/easylist.txt', 'resources/easyprivacy.txt', 'resources/fanboy-annoyance.txt']
rule_checker = rules.AdblockRules(rule_files=rule_files, skip_parsing_errors=True)

STUDY_PATH = Path("/home/martin/git/interactive_privacyscanner/study/")


def generate_csv():
    with open(STUDY_PATH / "results.csv", 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',')
        header = ['url',
                  'note',
                  'modal_present',
                  'banner_present',
                  # tp analysis
                  'tp_cookies_before',
                  'tp_cookies_after',
                  'tp_requests_before',
                  'tp_requests_after',
                  'tp_requests_total',
                  'tracking_tp_before',
                  'tracking_tp_after',
                  'tracking_tp_total',
                  'tracking_tp_additional',
                  'duration',
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

        results_path = STUDY_PATH / "data"
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
            user_note = result_d['user_note'].lower()
        row.append(user_note)  # note
        row.append(int(user_note.lower() == 'm'))  # modal_present
        row.append(int(user_note.lower() != 'x'))  # banner_present
    else:
        row += [-1] * 4

    # tp analysis
    analysis_file = result_path / "first_scan" / "analysis.json"
    analysis = utils.load_json(analysis_file)
    if analysis:
        row.append(analysis['tp_cookies_before'])
        row.append(analysis['tp_cookies_after'])
        row.append(analysis['tp_requests_before'])
        row.append(analysis['tp_requests_after'])
        row.append(analysis['tp_requests_total'])
        row.append(analysis['tracking_tp_before'])
        row.append(analysis['tracking_tp_after'])
        row.append(analysis['tracking_tp_total'])
        row.append(analysis['tracking_tp_additional'])
        row.append(analysis['duration'])
    else:
        row += [-1] * 10

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
    if -1 in row:
        # if one entry has error, set every entry to error
        row = row[:2] + [-1] * (len(row) - 2)
    return row


def analyze():
    path = STUDY_PATH / "data"
    i = 0

    tp_count_before = defaultdict(int)
    tp_count_additional = defaultdict(int)
    tp_count_total = defaultdict(int)
    tp_tracker_count_before = defaultdict(int)
    tp_tracker_count_additional = defaultdict(int)
    tp_tracker_count_total = defaultdict(int)

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
            results = analyze_interaction(scan_domain, interaction[0], interaction[1], analysis_filename)

            append_count(results['tp_requests_before'], tp_count_before)
            append_count(results['tp_requests_additional'], tp_count_additional)
            append_count(results['tp_requests_total'], tp_count_total)
            append_count(results['tracking_tp_before'], tp_tracker_count_before)
            append_count(results['tracking_tp_additional'], tp_tracker_count_additional)
            append_count(results['tracking_tp_total'], tp_tracker_count_total)
        i += 1

    header = ['domain', 'count']
    write_simple_csv("tp_count_before.csv", header, tp_count_before.items())
    write_simple_csv("tp_count_additional.csv", header, tp_count_additional.items())
    write_simple_csv("tp_count_total.csv", header, tp_count_total.items())
    write_simple_csv("tp_tracker_count_before.csv", header, tp_tracker_count_before.items())
    write_simple_csv("tp_tracker_count_additional.csv", header, tp_tracker_count_additional.items())
    write_simple_csv("tp_tracker_count_total.csv", header, tp_tracker_count_total.items())


def append_count(new_occ, count):
    for c in new_occ:
        count[c] += 1


def write_simple_csv(filename, header, items):
    path = STUDY_PATH / "tmp" / filename
    with open(path, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',')
        csv_writer.writerow(header)
        csv_writer.writerows(items)


def contains_tracker(urls):
    return any(map(lambda x: x[1], urls))


def analyze_interaction(scan_domain, interaction_before, interaction_after, path):
    # before
    tp_cookies_before = get_third_parties_c(scan_domain, interaction_before['cookies'])
    tp_requests_before = get_third_parties_r(scan_domain, interaction_before['requests'])
    tracking_tp_before = {k for k, v in tp_requests_before.items() if contains_tracker(v)}

    # after
    tp_cookies_after = get_third_parties_c(scan_domain, interaction_after['cookies'])
    tp_requests_after = get_third_parties_r(scan_domain, interaction_after['requests'])
    tracking_tp_after = {k for k, v in tp_requests_after.items() if contains_tracker(v)}

    tp_requests_combined = set(tp_requests_before.keys()).union(set(tp_requests_after.keys()))
    tp_requests_additional = set(tp_requests_after.keys()).difference(set(tp_requests_before.keys()))

    tracking_tp_combined = tracking_tp_after.union(tracking_tp_before)
    tracking_tp_additional = tracking_tp_after.difference(tracking_tp_before)

    tp_analysis = {
        "tp_cookies_before": len(tp_cookies_before),
        "tp_requests_before": len(tp_requests_before),
        "tracking_tp_before": len(tracking_tp_before),
        "tp_cookies_after": len(tp_cookies_after),
        "tp_requests_after": len(tp_requests_after),
        "tracking_tp_after": len(tracking_tp_after),
        "tp_requests_additional": len(tp_requests_additional),
        "tp_requests_total": len(tp_requests_combined),
        "tracking_tp_total": len(tracking_tp_combined),
        "tracking_tp_additional": len(tracking_tp_additional),
        "duration": interaction_after['timestamp'] - interaction_before['timestamp'],
    }
    tp_analysis_detailed = {
        "tp_cookies_before": list(tp_cookies_before),
        "tp_requests_before": list(tp_requests_before.keys()),
        "tracking_tp_before": list(tracking_tp_before),
        "tp_cookies_after": list(tp_cookies_after),
        "tp_requests_after": list(tp_requests_after.keys()),
        "tracking_tp_after": list(tracking_tp_after),
        "tp_requests_additional": list(tp_requests_additional),
        "tp_requests_total": list(tp_requests_combined),
        "tracking_tp_total": list(tracking_tp_combined),
        "tracking_tp_additional": list(tracking_tp_additional),
        "duration": interaction_after['timestamp'] - interaction_before['timestamp'],
    }

    analysis_path = path / "analysis.json"
    utils.store_json(analysis_path, tp_analysis)

    analysis_path_detailed = path / "analysis_detailed.json"
    utils.store_json(analysis_path_detailed, tp_analysis_detailed)

    return tp_analysis_detailed


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



if __name__ == "__main__":
    analyze()
    generate_csv()
