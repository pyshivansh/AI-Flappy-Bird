import pandas as pd
from sklearn.model_selection import train_test_split
from tensorflow import data
from xgboost import XGBRegressor
import os
import pickle

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
model_file = os.path.join("Assets", "AI_model.pkl")
complete_model = None

dataset = pd.read_csv(os.path.join("Assets", "data.csv"))
x = dataset.drop(columns=["Click_Y"])
y = dataset["Click_Y"]

x_train, x_rest, y_train, y_rest = train_test_split(x, y, test_size=0.2, shuffle=True)
x_valid, x_test, y_valid, y_test = train_test_split(x_rest, y_rest, test_size=0.5, shuffle=True)


def train_model():
    model = None
    if len(dataset) > 0:
        model = XGBRegressor(n_estimators=500, learning_rate=0.05, early_stopping_rounds=10)
        model.fit(x_train, y_train, eval_set=[(x_valid, y_valid)], verbose=False)
        predictions = model.predict(x_test)
        results = [i for i in y_test]
        loss = 0
        for i in range(0, len(y_test)):
            loss += abs(results[i]-predictions[i])
        with open(model_file, 'wb') as file:
            pickle.dump(model, file)
    return model
    #model = keras.models.Sequential()
    #model.add(keras.layers.BatchNormalization(input_shape=x.shape[1:]))
    #model.add(keras.layers.Dense(1024, activation='relu'))
    #model.add(keras.layers.BatchNormalization())
    #model.add(keras.layers.Dropout(rate=0.5))
    #model.add(keras.layers.Dense(1024, activation='relu'))
    #model.add(keras.layers.BatchNormalization())
    #model.add(keras.layers.Dropout(rate=0.5))
    #model.add(keras.layers.Dense(1024, activation='relu'))
    #model.add(keras.layers.BatchNormalization())
    #model.add(keras.layers.Dropout(rate=0.5))
    #model.add(keras.layers.Dense(1))
    
    model.compile(optimizer="adam", loss="mae")
    early_stopping = keras.callbacks.EarlyStopping(min_delta=1, patience=10, restore_best_weights=True)
    model.fit(x_train, y_train, epochs=1000, validation_data=[x_test, y_test], callbacks=[early_stopping], verbose=0)
    predictions = model.predict(x_test)
    results = [i for i in y_test]
    loss = 0
    for i in range(0, len(y_test)):
        print(predictions[i], results[i], results[i]-predictions[i])
        loss += abs(results[i]-predictions[i])
    with open(model_file, 'wb') as file:
        pickle.dump(model, file)
    return model

def return_model(new_model):
    if new_model:
        complete_model = train_model() 
    else:
        with open(model_file, 'rb') as file:
            complete_model = pickle.load(file)
        # predictions = complete_model.predict(x_test)
        # results = [i for i in y_test]
        # loss = 0
        # for i in range(0, len(y_test)):
        #     print(predictions[i], results[i], results[i]-predictions[i])
        #     loss += abs(results[i]-predictions[i])
        # print(loss/(len(y_test)))
    return complete_model
