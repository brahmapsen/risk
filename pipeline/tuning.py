import optuna
import xgboost as xgb
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split


def objective(trial, X, y):
    """Defines the search space and trains an XGBoost model on each trial."""

    param = {
        "objective": "binary:logistic",
        "eval_metric": "auc",
        "eta": trial.suggest_float("eta", 0.01, 0.3),
        "max_depth": trial.suggest_int("max_depth", 2, 10),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
        "lambda": trial.suggest_float("lambda", 0.1, 3.0),
        "alpha": trial.suggest_float("alpha", 0.1, 3.0),
        "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
    }

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    dtrain = xgb.DMatrix(X_train, label=y_train)
    dval = xgb.DMatrix(X_val, label=y_val)

    booster = xgb.train(
        params=param,
        dtrain=dtrain,
        evals=[(dval, "eval")],
        num_boost_round=trial.suggest_int("num_boost_round", 100, 500),
        verbose_eval=False
    )

    preds = booster.predict(dval)
    auc = roc_auc_score(y_val, preds)

    return auc


def tune_hyperparams(X, y, n_trials=25):
    """Runs Optuna tuning process."""
    study = optuna.create_study(direction="maximize")
    study.optimize(lambda trial: objective(trial, X, y), n_trials=n_trials)
    return study.best_params
