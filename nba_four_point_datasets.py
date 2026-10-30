#CLEANING DATASET
#Use dataset2_top50_3pm_by_distance.csv and dataset2_top50_3pm_summary.csv, other one is redundant
import pandas as pd
df = pd.read_csv('dataset2_top50_3pm_by_distance.csv')
print(df)