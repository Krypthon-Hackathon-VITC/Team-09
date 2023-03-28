from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.pipeline import Pipeline, make_pipeline

# ensemble model
class HOUSE_PRICE_PREDICTOR :
    def __init__(self) :
        # list of all models
        self.MODELS = [make_pipeline(StandardScaler(),
                                     PolynomialFeatures(3),
                                     RandomForestRegressor(criterion="friedman_mse",
                                                           max_depth=100,
                                                           min_samples_split=1,
                                                           min_samples_leaf=1))
                       ]

    def train(self, features, targets) :
        # train all the models in the list
        for _ in range(len(self.MODELS)) :
            self.MODELS[_].fit(features, targets)
        self.set_optimized(features, targets)

    def set_optimized(self, features, targets) :
        # set optimised model as the best model
        # and store its index to access it
        max_idx = 0
        max_acc = 0
        for _ in range(len(self.MODELS)) :
            acc = self.MODELS[_].score(features, targets)
            if acc > max_acc :
                max_acc = acc
                max_idx = _
        self.ACCURATE_MODEL = max_idx

    def predict(self, features) :
        # predict for features
        return self.MODELS[self.ACCURATE_MODEL].predict(features)

    def score(self, features, targets) :
        # get score of model
        return self.MODELS[self.ACCURATE_MODEL].score(features, targets)
