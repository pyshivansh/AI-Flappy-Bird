from pandas import DataFrame, read_csv
from os import path

# Load the dataset from the CSV file
dataset = read_csv(path.join("Assets", "data.csv"))
target_dataset = path.join("Assets", "new_data.csv")
dataset_cols = dataset.columns

# Adjust the data and save it to a new CSV file
for index, row in dataset.iterrows():
    curr_data = {}
    for col in dataset_cols:
        if col == "Accuracy":
            # Adjust the accuracy value
            actual_value = 1-(1-row[col])*2
            curr_data[col] = [round(actual_value, 4)]
        else:
            # Round other values to 1 decimal place
            curr_data[col] = [round(row[col], 1)]
    # Save the adjusted data to the new CSV file
    curr_dataframe = DataFrame(curr_data)
    curr_dataframe.to_csv(target_dataset, mode="a", index=False, header=False)