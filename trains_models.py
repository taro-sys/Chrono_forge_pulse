import pandas as pd
import numpy as np
import os
import pickle
import warnings
import sys

# Suppress warnings
warnings.filterwarnings("ignore")

try:
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense
    from xgboost import XGBRegressor
    import lightgbm as lgb
    from sklearn.preprocessing import MinMaxScaler
except ImportError as e:
    print(f"Error: Missing library. {e}")
    sys.exit(1)


def train_all_models(csv_path="sales_data.csv", model_dir="./models"):
    print(f"Loading data from {csv_path}...")

    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    df = pd.read_csv(csv_path)

    # Handle different column names
    if 'sales_value' in df.columns:
        data = df['sales_value'].values.astype(float)
    else:
        col_name = df.columns[1]
        print(f"Column 'sales_value' missing. Using '{col_name}'")
        data = df[col_name].values.astype(float)

    if not os.path.exists(model_dir):
        os.makedirs(model_dir)

    # --- SARIMA ---
    print("Training SARIMA...")
    try:
        model = SARIMAX(data, order=(1, 1, 1), seasonal_order=(0, 0, 0, 0))
        sarima_fit = model.fit(disp=False)
        with open(f"{model_dir}/sarima_model.pkl", "wb") as f:
            pickle.dump(sarima_fit, f)
    except Exception as e:
        print(f"SARIMA error: {e}")

    # --- LSTM ---
    print("Training LSTM...")
    try:
        if len(data) > 10:
            scaler = MinMaxScaler()
            scaled_data = scaler.fit_transform(data.reshape(-1, 1))

            X, y = [], []
            window_size = 5
            for i in range(len(scaled_data) - window_size):
                X.append(scaled_data[i:i + window_size])
                y.append(scaled_data[i + window_size])
            X, y = np.array(X), np.array(y)

            lstm = Sequential([
                LSTM(50, activation='relu', input_shape=(window_size, 1)),
                Dense(1)
            ])
            lstm.compile(optimizer='adam', loss='mse')
            lstm.fit(X, y, epochs=10, verbose=0)
            lstm.save(f"{model_dir}/lstm_model.keras")

            with open(f"{model_dir}/scaler.pkl", "wb") as f:
                pickle.dump(scaler, f)
        else:
            print("Not enough data for LSTM.")
    except Exception as e:
        print(f"LSTM error: {e}")

    # --- XGBoost ---
    print("Training XGBoost...")
    try:
        if len(data) > 6:
            X_reg = np.array([data[i:i + 5] for i in range(len(data) - 5)])
            y_reg = np.array([data[i + 5] for i in range(len(data) - 5)])

            xgb = XGBRegressor(n_estimators=50)
            xgb.fit(X_reg, y_reg)
            xgb.save_model(f"{model_dir}/xgb_model.json")
        else:
            print("Not enough data for XGBoost.")
    except Exception as e:
        print(f"XGBoost error: {e}")

    # --- LightGBM ---
    print("Training LightGBM...")
    try:
        if len(data) > 6:
            train_set = lgb.Dataset(X_reg, label=y_reg)
            params = {'objective': 'regression', 'metric': 'rmse', 'verbose': -1}
            lgb_model = lgb.train(params, train_set, num_boost_round=50)
            lgb_model.save_model(f"{model_dir}/lgbm_model.txt")
        else:
            print("Not enough data for LightGBM.")
    except Exception as e:
        print(f"LightGBM error: {e}")

    print(f"Done. Models saved to {model_dir}")


if __name__ == "__main__":
    train_all_models()