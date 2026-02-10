import os
import numpy as np
import pickle
import sys
from dataclasses import dataclass

try:
    import lightgbm as lgb
    from xgboost import XGBRegressor
    from tensorflow.keras.models import load_model
except ImportError as e:
    print(f"CRITICAL: Missing library {e}. Cannot run real forecast.")
    sys.exit(1)


@dataclass
class ForecastResult:
    prediction: float
    breakdown: dict
    confidence_score: float


class HybridForecastingEngine:
    def __init__(self, model_dir="./models"):
        self.model_dir = model_dir
        self._load_models()

    def _load_models(self):
        print("[System] Loading Real Forecasting Models...")

        required_files = ["sarima_model.pkl", "lstm_model.keras", "scaler.pkl", "xgb_model.json", "lgbm_model.txt"]
        for f in required_files:
            if not os.path.exists(os.path.join(self.model_dir, f)):
                print(f"FATAL: Model file missing: {f}")
                print("Run 'train_models.py' first.")
                sys.exit(1)

        try:
            with open(f"{self.model_dir}/sarima_model.pkl", "rb") as f:
                self.sarima = pickle.load(f)

            self.lstm = load_model(f"{self.model_dir}/lstm_model.keras")
            with open(f"{self.model_dir}/scaler.pkl", "rb") as f:
                self.scaler = pickle.load(f)

            self.xgb = XGBRegressor()
            self.xgb.load_model(f"{self.model_dir}/xgb_model.json")

            self.lgbm = lgb.Booster(model_file=f"{self.model_dir}/lgbm_model.txt")
            print("All binary models loaded successfully.")

        except Exception as e:
            print(f"FATAL: Corrupt model file. {e}")
            sys.exit(1)

    def generate_forecast(self, recent_data):
        results = {}

        # SARIMA
        try:
            pred = self.sarima.forecast(steps=1)
            results["SARIMA"] = float(pred[0])
        except:
            results["SARIMA"] = 0

        # LSTM
        try:
            last_5 = recent_data[-5:].reshape(-1, 1)
            scaled = self.scaler.transform(last_5).reshape(1, 5, 1)
            pred_scaled = self.lstm.predict(scaled, verbose=0)
            pred = self.scaler.inverse_transform(pred_scaled)
            results["LSTM"] = float(pred[0][0])
        except:
            results["LSTM"] = 0

        # XGBoost & LightGBM
        try:
            features = recent_data[-5:].reshape(1, -1)
            results["XGBoost"] = float(self.xgb.predict(features)[0])
            results["LightGBM"] = float(self.lgbm.predict(features)[0])
        except:
            pass

        valid_preds = [v for v in results.values() if v > 0]
        if not valid_preds:
            return ForecastResult(0.0, results, 0.0)

        final_pred = np.mean(valid_preds)
        std_dev = np.std(valid_preds)
        conf = max(0, 100 - (std_dev / final_pred * 200))

        return ForecastResult(final_pred, results, conf)