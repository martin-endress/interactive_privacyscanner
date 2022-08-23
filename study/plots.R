library(tidyverse)
library(ggplot2)

# define color pallet
# usage:
#   scale_fill_manual() for box plot, bar plot, violin plot, dot plot, etc
#   scale_color_manual() for lines and points
ubblue = "#00457D"
ubblue80 = "#336A97"
ubblue60 = "#668FB1"
ubblue40 = "#99B5CB"
ubblue20 = "#CCDAE5"
ubyellow = "#FFD300"
ubyellow25 = "#FFF4BF"
ubred = "#e6444F"
ubgreen = "#97BF0D"
color_pallete = sample(
  c(
    ubblue,
    ubblue80,
    ubblue60,
    ubblue40,
    ubblue20,
    ubyellow,
    ubyellow25,
    ubred,
    ubgreen
  )
)

# load data
data = read.csv(file = "./git/interactive_privacyscanner/study/results.csv",
                sep = ",",
                na.strings = "-1")
# change scale
data$modal_present = as.logical(data$modal_present)
data$banner_present = as.logical(data$banner_present)

# calculate
data = data %>%
  mutate(banner = factor(
    case_when(
      modal_present ~ "modal",
      (!modal_present &
         banner_present) ~ "note",
      !banner_present ~ "no note",
      TRUE ~ "scan failed"
    )
  ))

banner_count_table = as.data.frame(table(data$banner))
banner_count_table$t = c("a")


# stacked bar plot
ggplot(banner_count_table, aes(fill = Var1, y = Freq, x = 'asdf')) +
  geom_bar(position = "fill", stat = "identity") +
  coord_flip() +
  scale_fill_manual(values = color_pallete)
