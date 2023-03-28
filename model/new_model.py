import joblib
import pandas as pd

from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

url = "https://raw.githubusercontent.com/mridulrb/Predict-loan-eligibility-using-IBM-Watson-Studio/master/Dataset/train_ctrUa4K.csv"


# ensemble model
class HOUSE_PRICE_PREDICTOR:
    def __init__(self):
        # list of all models
        # self.MODELS = [make_pipeline(StandardScaler(),
        #                              PolynomialFeatures(3),
        #                              RandomForestRegressor(criterion="friedman_mse",
        #                                                    max_depth=100,
        #                                                    min_samples_split=1,
        #                                                    min_samples_leaf=1))
        #    ]
        self.MODELS = [make_pipeline(StandardScaler(),
                                     HistGradientBoostingRegressor(loss="squared_error",
                                                                   max_depth=100,
                                                                   min_samples_leaf=1)
                                     )]

    def train(self, features, targets):
        # train all the models in the list
        for _ in range(len(self.MODELS)):
            self.MODELS[_].fit(features, targets)
        self.set_optimized(features, targets)

    def set_optimized(self, features, targets):
        # set optimised model as the best model
        # and store its index to access it
        max_idx = 0
        max_acc = 0
        for _ in range(len(self.MODELS)):
            acc = self.MODELS[_].score(features, targets)
            if acc > max_acc:
                max_acc = acc
                max_idx = _
        self.ACCURATE_MODEL = max_idx

    def predict(self, features):
        # predict for features
        return self.MODELS[self.ACCURATE_MODEL].predict(features)

    def score(self, features, targets):
        # get score of model
        return self.MODELS[self.ACCURATE_MODEL].score(features, targets)

def train():
    FEATURES = []
    TARGETS = []
    LOANS_REQUESTED = pd.read_csv(url)
    
    LOANS_REQUESTED["Loan_Status"] = LOANS_REQUESTED["Loan_Status"] == "Y"
    LOANS_REQUESTED["Gender"] = LOANS_REQUESTED["Gender"] == "Male"
    LOANS_REQUESTED["Married"] = LOANS_REQUESTED["Married"] == "Yes"
    LOANS_REQUESTED["Education"] = LOANS_REQUESTED["Education"] == "Graduate"
    LOANS_REQUESTED["Self_Employed"] = LOANS_REQUESTED["Self_Employed"] == "Yes"
    LOANS_REQUESTED["Property_Area"] = LOANS_REQUESTED["Property_Area"] == "Urban"
    LOANS_REQUESTED["Dependents"] = LOANS_REQUESTED["Dependents"].apply(
        lambda x: "3" if x == "3+" else x)
    
    for index, row in LOANS_REQUESTED.iterrows():
        FEATURES.append([])
        FEATURES[-1].append(row["Gender"])
        FEATURES[-1].append(row["Married"])
        FEATURES[-1].append(row["Dependents"])
        FEATURES[-1].append(row["Education"])
        FEATURES[-1].append(row["Self_Employed"])
        FEATURES[-1].append(row["ApplicantIncome"])
        FEATURES[-1].append(row["CoapplicantIncome"])
        FEATURES[-1].append(row["LoanAmount"])
        FEATURES[-1].append(row["Loan_Amount_Term"])
        FEATURES[-1].append(row["Property_Area"])
    
        TARGETS.append(row["Loan_Status"])
    # create model object
    MODEL = HOUSE_PRICE_PREDICTOR()
    # train
    MODEL.train(FEATURES, TARGETS)
    # print accuracy
    print("[ % ] SCORE IS", MODEL.score(FEATURES, TARGETS))
    print(type(MODEL.MODELS[MODEL.ACCURATE_MODEL]))
    # exit(0)
    # open a file and save the pickle of model
    joblib.dump(MODEL.MODELS[MODEL.ACCURATE_MODEL], "MODEL.pkl")
    

train()
