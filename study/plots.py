# libraries
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

out_path = Path("../../psi-exposee-master/degree-thesis/en/figures/study/")

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

# transform data
df['note'] = np.where(df['note'].isnull(), '', df.note)
df.dropna(inplace=True)

# create banner column
conditions = [df['note'] == 'm', df['note'] == '', df['note'] == 'x']
values = ['modal', 'banner', 'no banner']
df['banner'] = np.select(conditions, values)

# figure banner
fig, ax = plt.subplots(figsize=(3, 2.5))
df['banner'] \
    .value_counts() \
    .sort_index(ascending=False) \
    .plot(ax=ax, kind='bar', color=[ubyellow25, ubred, ubblue40], rot=0, width=0.5)
plt.savefig(out_path / 'banner_types.pdf')

