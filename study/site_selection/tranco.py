import random

import requests

TRANCO_CSV_FILENAME = "tranco_JX8KY.csv"

def main():
    tranco_list = get_tranco()
    de_list = apply_domain_filter(tranco_list, 'de')
    sample = random_sample(de_list, 300, 1_000)
    with open('domains.txt', "w") as f:
        with open('domains_error.txt', "w") as f_e:
            for l in sample:
                urls = [f'https://{l}', f'https://www.{l}', f'http://{l}', f'https://www.{l}']
                u = find_first(urls)
                if u:
                    f.write(u)
                    f.write('\n')
                else:
                    f_e.write(l)
                    f_e.write('\n')


def find_first(urls):
    for u in urls:
        if site_available(u):
            return u
    return None


def site_available(url):
    try:
        print(f'trying {url}')
        r = requests.get(url, timeout=5)
        print(r.status_code)
        return 200 <= r.status_code < 300
    except Exception as e:
        return False


def random_sample(lst, n, max):
    if n > len(lst) or n > max:
        print('illegal input')
        return []
    return random.sample(lst[:max], n)


def apply_domain_filter(lst, domain):
    f = lambda url: url.endswith(f'.{domain}')
    return list(filter(f, lst))


def get_tranco():
    with open(TRANCO_CSV_FILENAME, mode="r") as top1m_file:
        lines = top1m_file.readlines()
        return [line[line.find(',') + 1:].rstrip() for line in lines]


if __name__ == "__main__":
    main()
