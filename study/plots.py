# libraries
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

out_path = Path("../../psi-exposee-master/degree-thesis/en/figures/study/")


def cmp(a, b):
    return (a > b) - (a < b)


def map_cmp(lst):
    return map(lambda x: cmp(x, 0), lst)


matplotlib.style.use('ggplot')

# define colors
ubblue = "#00457D"
ubblue80 = "#336A97"
ubblue60 = "#668FB1"
ubblue40 = "#99B5CB"
ubblue20 = "#CCDAE5"
ubyellow = "#FFD300"
ubyellow25 = "#FFF4BF"
ubred = "#e6444F"
ubgreen = "#97BF0D"
color_pallete = [ubblue80, ubyellow, ubblue40, ubred, ubgreen, ubblue, ubblue60, ubblue20, ubyellow25]

# read data from CSV
df = pd.read_csv("results.csv", delimiter=',', na_values='-1')
n = len(df)

# transform data
df['note'] = np.where(df['note'].isnull(), '', df.note)
df.dropna(inplace=True)

# create banner column
conditions = [df['note'] == 'm', df['note'] == '', df['note'] == 'x']
values = ['modal', 'banner', 'no banner']
df['banner'] = np.select(conditions, values)

num_columns = ['additional_trackers', 'tp_cookies_after', 'tp_cookies_before', 'tp_requests_after',
               'tp_requests_before', 'tracking_tp_after', 'tracking_tp_before', 'tp_id_leaks_before',
               'tp_cookie_sync_before', 'fingerprinting_before', 'tp_id_leaks_after', 'tp_cookie_sync_after',
               'fingerprinting_after']

pivot = df.apply(lambda x: map_cmp(x) if x.name in num_columns else x) \
    .apply(np.sum)

no_leak = [n - pivot['tp_id_leaks_before'], n - pivot['tp_id_leaks_after']]
leak = [pivot['tp_id_leaks_before'] - pivot['tp_cookie_sync_before'],
        pivot['tp_id_leaks_after'] - pivot['tp_cookie_sync_after']]
cookie_sync = [pivot['tp_cookie_sync_before'], pivot['tp_cookie_sync_after']]

piv_no_tracking = [n - pivot['tracking_tp_before'], n - pivot['tracking_tp_after']]
piv_tracking = [pivot['tracking_tp_before'], pivot['tracking_tp_after'] - pivot['additional_trackers']]
piv_additional = [pivot['additional_trackers'] - pivot['additional_trackers'], pivot['additional_trackers']]

leak_before = [n - pivot['tp_id_leaks_before'],
               pivot['tp_id_leaks_before'] - pivot['tp_cookie_sync_before'],
               pivot['tp_cookie_sync_before']]

leak_after = [n - pivot['tp_id_leaks_after'],
              pivot['tp_id_leaks_after'] - pivot['tp_cookie_sync_after'],
              pivot['tp_cookie_sync_after']]


def plot_banner():
    fig, ax = plt.subplots(figsize=(3, 2.5))
    df['banner'] \
        .value_counts() \
        .sort_index(ascending=False) \
        .plot(ax=ax, kind='bar', color=[ubyellow25, ubred, ubblue40], rot=0, width=0.5)
    plt.savefig(out_path / 'banner_types.pdf')


def plot_leak():
    fig, ax = plt.subplots(figsize=(3.6, 3))
    #    fig, ax = plt.subplots(figsize=(5, 3.5))

    labels = ['before consent', 'after consent']
    width = 0.25  # the width of the bars: can also be len(x) sequence

    # reverse order for legend
    ax.bar(labels, cookie_sync, width, bottom=np.add(leak, no_leak), label='cookie syncing', color=ubred)
    ax.bar(labels, leak, width, bottom=no_leak, label='ID leak', color=ubyellow25)
    ax.bar(labels, no_leak, width, label='no leak', color=ubblue40)

    ax.set_ylabel('Websites')
    # ax.set_title('Websites exhibiting ID leaking and syncing')
    ax.legend()
    ax.set_position([0.175, 0.13, 0.8, 0.8])

    plt.savefig(out_path / 'leak.pdf')


def plot_tp():
    fig, ax = plt.subplots(figsize=(5.2, 4))

    colors = [ubblue40, ubyellow25, ubgreen]

    ax, props = df \
        .rename(columns=
                {"tp_requests_before": "before consent",
                 "tp_requests_after": "after consent",
                 "additional_trackers": "total"}) \
        .plot(kind='box',
              column=['before consent', 'after consent', 'total'],
              medianprops=dict(linestyle='-', linewidth=1.5, color='black'),
              color=dict(boxes='black', whiskers='black', medians='black', caps='black'),
              patch_artist=True,
              return_type='both',
              showfliers=False,
              ax=ax)
    for patch, color in zip(props['boxes'], colors):
        patch.set_facecolor(color)

    plt.yticks(np.arange(0, 71, 10))
    ax.set_ylim(0, 70)
    ax.set_ylabel('Third-parties')

    ax.set_position([0.19, 0.1, 0.8, 0.815])

    plt.savefig(out_path / 'third_party_box.pdf')


def plot_tracking():
    fig, ax = plt.subplots(figsize=(3.6, 3))

    labels = ['before consent', 'after consent']
    width = 0.25  # the width of the bars: can also be len(x) sequence

    ax.bar(labels, piv_tracking, width,
           bottom=np.add(piv_additional, piv_no_tracking),
           label='tracking', color=ubred)
    ax.bar(labels, piv_additional, width,
           bottom=piv_no_tracking,
           label='add tracking', color=ubyellow25)
    ax.bar(labels, piv_no_tracking, width,
           label='no tracking', color=ubblue40)

    ax.set_ylabel('Websites')
    ax.set_position([0.175, 0.13, 0.8, 0.8])
    ax.legend()
#    plt.show()
    plt.savefig(out_path / 'tracking_tp.pdf')


#plot_tp()
#plot_leak()
#plot_banner()
#plot_tracking()

print(piv_tracking)
print(piv_additional)
