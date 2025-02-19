from pandas import DataFrame, read_csv
from os import path

dataset = read_csv(path.join("Assets", "data.csv"))
dataset_cols = list(dataset.columns)

for i in dataset_cols:
    decimal_places = 1
    if i == "Accuracy":
        decimal_places = 4
    for j in range(len(dataset[i])):
        dataset.replace(to_replace=dataset[i][j], value=round(dataset[i][j], decimal_places), inplace=True)

dataset.to_csv(path.join("Assets", "new_data.csv"), index=False)

        