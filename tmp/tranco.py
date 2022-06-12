import random


def main():
    for e in get_tranco(5,top=1000):
        print(e[e.find(',')+1:])


def get_tranco(n, top=None):
    with open('top-1m.csv', mode="r") as top1m_file:
        lines = top1m_file.readlines()
        lines = [line.rstrip() for line in lines]
        if top is not None:
            lines = lines[:top]
        return random.sample(lines, n)


if __name__ == "__main__":
    main()
