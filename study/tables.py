# libraries
from pathlib import Path

import latextable
import matplotlib
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from texttable import Texttable

OUT_PATH = Path("../../psi-exposee-master/degree-thesis/en/figures/study/")


def print_table():
    header = ['\\#', 'before consent', 'after consent (additional)', 'after consent (total)']
    header_bf = list(map(lambda x: '\\tabhead{' + x + '}', header))
    n = 6
    n_total = 251
    result_before = get_top_entries('tp_tracker_count_before.csv', n)
    result_additional = get_top_entries('tp_tracker_count_additional.csv', n)
    result_total = get_top_entries('tp_tracker_count_total.csv', n)

    table = Texttable()
    table.set_deco(Texttable.HEADER)
    table.set_cols_align("clll")
    table.header(header_bf)
    for i in range(n):
        table.add_row([str(i + 1) + ")",
                       strip_www(result_before[i][0]),
                       strip_www(result_additional[i][0]),
                       strip_www(result_total[i][0])])

        table.add_row(['',
                       "{:.1f}\\%".format(round(result_before[i][1] * 100 / n_total, 1)),
                       "{:.1f}\\%".format(round(result_additional[i][1] * 100 / n_total, 1)),
                       "{:.1f}\\%".format(round(result_total[i][1] * 100 / n_total, 1))])

        print('DEBUG TABLE')
        print(table.draw())

        print('TODOs')
        print('add top-mid-bottomrule, make wide*, [t], title to top, footnotesize')

        with open(OUT_PATH / 'tracking_table.tex', 'w') as f:
            t = latextable.draw_latex(table,
                                      caption="Top six third parties classified as trackers embedded in websites. Additional trackers are only seen after consent, total refer to all trackers across the interaction.",
                                      label="tab:study:top_third_parties")
            f.write(t)


def strip_www(url):
    if url[:4] == 'www.':
        return url[4:]
    return url


def get_top_entries(filename, n):
    return pd \
               .read_csv(filename, delimiter=',') \
               .sort_values(by='count', ascending=False) \
               .iloc[:n] \
        .values \
        .tolist()


df = pd.read_csv("tp_tracker_count_total.csv", delimiter=',')

if __name__ == "__main__":
    print_table()
