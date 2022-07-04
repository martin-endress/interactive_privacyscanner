import random

TRANCO_CSV_FILENAME = "tranco_JX8KY.csv"


def main():
    tranco_list = get_tranco()
    de_list = apply_domain_filter(tranco_list, 'de')
    sample = random_sample(de_list, 100)
    print(sample)


def random_sample(lst, n):
    # todo define max
    if n > len(lst):
        print('ERROR, n>len(lst)')
        return []
    return random.sample(lst, n)


def apply_domain_filter(lst, domain):
    f = lambda url: url.endswith(f'.{domain}')
    return list(filter(f, lst))


def get_tranco():
    with open(TRANCO_CSV_FILENAME, mode="r") as top1m_file:
        lines = top1m_file.readlines()
        return [line[line.find(',') + 1:].rstrip() for line in lines]


if __name__ == "__main__":
    main()
