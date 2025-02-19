import pandas as pd
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
import os
import pickle

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# Define the path to the model file
model_file = os.path.join("Assets", "AI_model.pkl")
complete_model = None

# Load the dataset from the CSV file
dataset = pd.read_csv(os.path.join("Assets", "data.csv"))

# Split the dataset into features (x) and target (y)
x = dataset.drop(columns=["Click_Y"])
y = dataset["Click_Y"]

# Split the data into training, validation, and test sets
x_train, x_rest, y_train, y_rest = train_test_split(x, y, test_size=0.2, shuffle=True)
x_valid, x_test, y_valid, y_test = train_test_split(x_rest, y_rest, test_size=0.5, shuffle=True)

# Function to train the XGBoost model
def train_model():
    model = None
    if len(dataset) > 0:
        # Initialize the XGBoost model
        model = XGBRegressor(n_estimators=500, learning_rate=0.05, early_stopping_rounds=10)
        # Train the model
        model.fit(x_train, y_train, eval_set=[(x_valid, y_valid)], verbose=False)
        # Make predictions on the test set
        predictions = model.predict(x_test)
        results = [i for i in y_test]
        loss = 0
        # Calculate the loss
        for i in range(0, len(y_test)):
            loss += abs(results[i]-predictions[i])
        # Save the trained model to a file
        with open(model_file, 'wb') as file:
            pickle.dump(model, file)
    return model

# Function to return the trained model
def return_model(new_model):
    if new_model:
        # Train a new model if requested
        complete_model = train_model() 
    else:
        # Load the existing model from the file
        with open(model_file, 'rb') as file:
            complete_model = pickle.load(file)
    return complete_model