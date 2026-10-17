# evaluate_model(model, X, y, splitter, groups=None) -> (fold_df, summary)
# Purpose: score a scikit-learn model with cross-validation, no leakage.
# Inputs:
#   model: any sklearn-style estimator (fit/predict), or a Pipeline
#   X: pandas DataFrame of features, y: pandas Series of target (Price_yen)
#   splitter: KFold or GroupKFold instance
#   groups: pandas Series of group labels, or None for KFold
# For each fold from splitter.split(X, y, groups):
#   - clone(model) fresh for every fold (from sklearn.base import clone)
#   - fit on X.iloc[train_idx], y.iloc[train_idx] ONLY
#   - predict on X.iloc[test_idx]
#   - compute MAE, RMSE (sqrt of mean_squared_error), R2 on the test fold
#   - if groups is not None, assert the train and test group sets do not overlap
# Return:
#   fold_df: DataFrame with one row per fold and columns mae, rmse, r2
#   summary: dict with mean and std of each metric
# Do not fit anything (imputer, encoder, scaler) outside the fold loop.
# Do not shuffle or modify X or y. Never use the test fold for any fitting.
def evaluate_model(model, X, y, splitter, groups=None):
    from sklearn.base import clone
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    import numpy as np
    import pandas as pd

    fold_results = []
    
    for train_idx, test_idx in splitter.split(X, y, groups):
        # Clone the model to ensure a fresh instance for each fold
        model_clone = clone(model)
        
        # Split the data into training and testing sets
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        # Fit the model on the training data
        model_clone.fit(X_train, y_train)
        
        # Predict on the test data
        y_pred = model_clone.predict(X_test)
        
        # Calculate metrics
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        # Store results for this fold
        fold_results.append({'mae': mae, 'rmse': rmse, 'r2': r2})
        
        # If groups are provided, check for overlap between train and test groups
        if groups is not None:
            train_groups = set(groups.iloc[train_idx])
            test_groups = set(groups.iloc[test_idx])
            assert train_groups.isdisjoint(test_groups), "Train and test groups overlap!"
    
    # Create a DataFrame from the fold results
    fold_df = pd.DataFrame(fold_results)
    
    # Calculate summary statistics
    summary = {
        'mae_mean': fold_df['mae'].mean(),
        'mae_std': fold_df['mae'].std(),
        'rmse_mean': fold_df['rmse'].mean(),
        'rmse_std': fold_df['rmse'].std(),
        'r2_mean': fold_df['r2'].mean(),
        'r2_std': fold_df['r2'].std()
    }
    
    return fold_df, summary



