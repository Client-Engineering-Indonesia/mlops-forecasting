from sklearn.feature_selection import mutual_info_regression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import root_mean_squared_error, r2_score

from xgboost import XGBRegressor
from xgboost.callback import EarlyStopping

import pandas as pd
import numpy as np


def mi_feature_selection(X: pd.DataFrame, y, top_k=15):
    mi = mutual_info_regression(X, y, random_state=42)
    scores = pd.Series(mi, index=X.columns)
    return scores.sort_values(ascending=False).head(top_k).index.tolist()


def tree_feature_selection(
    X: pd.DataFrame,
    y: pd.Series,
    top_k: int = 10
):
    model = RandomForestRegressor(
        n_estimators=200,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X, y)

    importances = pd.Series(
        model.feature_importances_,
        index=X.columns
    )

    selected_features = importances.sort_values(
        ascending=False
    ).head(top_k).index.tolist()

    return selected_features

def correlation_pruning(X: pd.DataFrame, threshold=0.9):
    corr = X.corr().abs()
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))

    to_drop = [
        column for column in upper.columns
        if any(upper[column] > threshold)
    ]

    return {
        "dropped_features": to_drop,
        "remaining_features": [c for c in X.columns if c not in to_drop]
    }


def train_xgboost_regressor(
    X,
    y,
    test_size=0.2,
    random_state=42
):
    # 1️⃣ Train / validation split
    X_train, X_val, y_train, y_val = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        shuffle=False  # IMPORTANT for time-series
    )

    # 2️⃣ Model
    model = XGBRegressor(
        n_estimators=1000,
        learning_rate=0.05,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="reg:squarederror",
        eval_metric="rmse",
        callbacks=[EarlyStopping(rounds=50, save_best=True)],  # ✅ HERE
        random_state=42,
        n_jobs=-1
    )

    model.fit(
        X_train,
        y_train,
        eval_set=[(X_val, y_val)],
        verbose=False
    )

    # 4️⃣ Evaluate
    y_pred_train = model.predict(X_train)
    y_pred_val = model.predict(X_val)

    X_train["pred"] = y_pred_train
    X_val["pred"] = y_pred_val

    metrics = {
        "training_result": {
            "rmse": float(root_mean_squared_error(y_train, y_pred_train)),
            "r2": r2_score(y_train, y_pred_train),
        },
        "testing_result": {
            "rmse": float(root_mean_squared_error(y_val, y_pred_val)),
            "r2": r2_score(y_val, y_pred_val),
        }
        
    }

    return model, metrics, X_train, X_val


def create_model_pipeline(X, y):
    mi_result = mi_feature_selection(X, y)
    rf_result = tree_feature_selection(X, y)
    prun_result = correlation_pruning(X)

    selected_features = mi_result + rf_result + prun_result["remaining_features"]
    selected_features = list(dict.fromkeys(selected_features))

    model, metrics, X_train, X_val = train_xgboost_regressor(X[selected_features], y)


    return {
        "selected_features": selected_features,
        "model": model,
        "metrics": metrics,
        "prediction": pd.concat([X_train, X_val]),
    }