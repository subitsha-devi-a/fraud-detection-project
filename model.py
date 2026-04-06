import pandas as pd
from sklearn.linear_model import LogisticRegression
import pickle

data = {
    "time_diff": [1,2,3,5,6,7,1,2],
    "click_count": [1,2,3,1,1,2,4,5],
    "is_fraud": [1,1,1,0,0,0,1,1]
}

df = pd.DataFrame(data)

X = df[["time_diff", "click_count"]]
y = df["is_fraud"]

model = LogisticRegression()
model.fit(X, y)

pickle.dump(model, open("model.pkl", "wb"))

print("Model trained")
