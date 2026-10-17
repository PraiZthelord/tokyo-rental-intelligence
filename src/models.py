# class MedianByGroup(BaseEstimator, RegressorMixin)
# Imports: from sklearn.base import BaseEstimator, RegressorMixin
# __init__(self, column="municipality"): store column as a plain attribute.
# fit(X, y): X is a pandas DataFrame, y a Series aligned with X.
#   Compute the median of y per value of X[self.column], using ONLY the data passed in.
#   Store as self.medians_ (dict). Store the overall median of y as self.global_median_.
#   Return self.
# predict(X): map X[self.column] to self.medians_; any value not seen in fit
#   (or missing) gets self.global_median_. Return a numpy array of floats.
# Do not use any column other than self.column. Do not read y in predict.
# Never fit on data passed to predict.

from sklearn.base import BaseEstimator, RegressorMixin
class MedianByGroup(BaseEstimator, RegressorMixin):
    def __init__(self, column="municipality"):
        self.column = column

    def fit(self, X, y):
        # Compute the median of y for each group in X[self.column]
        self.medians_ = y.groupby(X[self.column]).median().to_dict()
        # Compute the overall median of y
        self.global_median_ = y.median()
        return self

    def predict(self, X):
        # Map X[self.column] to the corresponding median values
        predictions = X[self.column].map(self.medians_)
        # Fill missing values with the overall median
        predictions.fillna(self.global_median_, inplace=True)
        return predictions.values



# Build a scikit-learn Pipeline called linear_pipe, then run it through evaluate_model twice.
# Imports: Pipeline, ColumnTransformer, SimpleImputer, OneHotEncoder, StandardScaler, LinearRegression.
#
# Numeric columns: ["area_m2", "age_years", "floor_min", "stories_above", "walk_min_nearest"]
#   -> SimpleImputer(strategy="median", add_indicator=True), then StandardScaler()
# Categorical column: ["municipality"]
#   -> OneHotEncoder(handle_unknown="ignore")
# Combine with ColumnTransformer, then LinearRegression().
#
# X = df[numeric cols + ["municipality"]], y = df["Price_yen"]
# Run through evaluate_model:
#   1. KFold(n_splits=5, shuffle=True, random_state=0), groups=None
#   2. GroupKFold(n_splits=5), groups=df["group_coarse"]   <- must pass groups=
# Print one small table: split name, mean MAE, mean RMSE, mean R2, std MAE.
# Print the split name from a separate variable.
# Do not fit the imputer, scaler or encoder outside the pipeline.
# Do not modify evaluate_model.

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LinearRegression

linear_pipe = Pipeline([
    ('preprocessor', ColumnTransformer(
        transformers=[
            ('num', Pipeline([
                ('imputer', SimpleImputer(strategy="median", add_indicator=True)),
                ('scaler', StandardScaler())
            ]), ["area_m2", "age_years", "floor_min", "stories_above", "walk_min_nearest"]),
            ('cat', OneHotEncoder(handle_unknown="ignore"), ["municipality"])
        ]
    )),
    ('regressor', LinearRegression())
])




# Build a scikit-learn Pipeline called rf_pipe in src/models.py.
# Imports: Pipeline, ColumnTransformer, SimpleImputer, OneHotEncoder, RandomForestRegressor.
#
# Numeric columns: ["area_m2", "age_years", "floor_min", "stories_above", "walk_min_nearest"]
#   -> SimpleImputer(strategy="median", add_indicator=True). No scaler (trees don't need it).
# Categorical column: ["municipality"]
#   -> OneHotEncoder(handle_unknown="ignore")
# Combine with ColumnTransformer, then
#   RandomForestRegressor(n_estimators=200, min_samples_leaf=3, n_jobs=-1, random_state=0).
# Do not fit anything outside the pipeline. Do not tune anything yet.
from sklearn.ensemble import RandomForestRegressor

rf_pipe = Pipeline([
    ('preprocessor', ColumnTransformer(
        transformers=[
            ('num', Pipeline([
                ('imputer', SimpleImputer(strategy="median", add_indicator=True))
            ]), ["area_m2", "age_years", "floor_min", "stories_above", "walk_min_nearest"]),
            ('cat', OneHotEncoder(handle_unknown="ignore"), ["municipality"])
        ]
    )),
    ('regressor', RandomForestRegressor(n_estimators=200, min_samples_leaf=3, n_jobs=-1, random_state=0))
])


# Build a scikit-learn Pipeline called xgb_pipe in src/models.py.
# Imports: Pipeline, ColumnTransformer, OneHotEncoder, XGBRegressor (from xgboost).
#
# Numeric columns: ["area_m2", "age_years", "floor_min", "stories_above", "walk_min_nearest"]
#   -> passthrough (XGBoost handles NaN natively; no imputer, no scaler)
# Categorical column: ["municipality"]
#   -> OneHotEncoder(handle_unknown="ignore")
# Then XGBRegressor(n_estimators=400, learning_rate=0.1, max_depth=6,
#   n_jobs=-1, random_state=0, tree_method="hist").
# Do not tune anything yet. Do not fit anything outside the pipeline.

from xgboost import XGBRegressor

xgb_pipe = Pipeline([
    ('preprocessor', ColumnTransformer(
        transformers=[
            ('num', 'passthrough', ["area_m2", "age_years", "floor_min", "stories_above", "walk_min_nearest"]),
            ('cat', OneHotEncoder(handle_unknown="ignore"), ["municipality"])
        ]
    )),
    ('regressor', XGBRegressor(n_estimators=400, learning_rate=0.1, max_depth=6,
                               n_jobs=-1, random_state=0, tree_method="hist",device="cuda"))
])