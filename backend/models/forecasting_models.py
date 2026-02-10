"""Forecasting models wrapper integrating existing ChronoForge models"""
import sys
import os
import numpy as np
import pandas as pd
import pickle
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

# Add parent directory to path to import existing modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import ML libraries with graceful fallback
TENSORFLOW_AVAILABLE = False
PROPHET_AVAILABLE = False
XGBOOST_AVAILABLE = False
LIGHTGBM_AVAILABLE = False
STATSMODELS_AVAILABLE = False
SKLEARN_AVAILABLE = False

try:
    from tensorflow.keras.models import load_model, Sequential
    from tensorflow.keras.layers import LSTM, Dense
    TENSORFLOW_AVAILABLE = True
except ImportError:
    print("⚠️  TensorFlow not available - LSTM model disabled")

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    print("⚠️  Prophet not available - Prophet model disabled")

try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    print("⚠️  XGBoost not available - XGBoost model disabled")

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    print("⚠️  LightGBM not available - LightGBM model disabled")

try:
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    STATSMODELS_AVAILABLE = True
except ImportError:
    print("⚠️  statsmodels not available - ARIMA model disabled")

try:
    from sklearn.preprocessing import MinMaxScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    print("⚠️  scikit-learn not available - some features disabled")


@dataclass
class ModelPrediction:
    """Single model prediction result"""
    model_name: str
    prediction: float
    confidence: float = 0.0
    error: Optional[str] = None


@dataclass
class EnsembleResult:
    """Ensemble forecast result"""
    predictions: List[float]
    model_breakdown: Dict[str, List[float]]
    best_model: str
    metrics: Dict[str, float]
    confidence_intervals: Dict[str, List[float]]


class ForecastingModels:
    """Wrapper for all forecasting models"""
    
    def __init__(self, model_dir: str = "../models"):
        self.model_dir = model_dir
        self.models_loaded = False
        
    def load_pretrained_models(self):
        """Load pre-trained models if available"""
        if self.models_loaded:
            return
            
        try:
            model_files = {
                "sarima": "sarima_model.pkl",
                "lstm": "lstm_model.keras",
                "scaler": "scaler.pkl",
                "xgb": "xgb_model.json",
                "lgbm": "lgbm_model.txt"
            }
            
            # Check if models exist
            all_exist = all(
                os.path.exists(os.path.join(self.model_dir, f)) 
                for f in model_files.values()
            )
            
            if all_exist:
                # Load SARIMA
                with open(f"{self.model_dir}/sarima_model.pkl", "rb") as f:
                    self.sarima = pickle.load(f)
                
                # Load LSTM
                self.lstm = load_model(f"{self.model_dir}/lstm_model.keras")
                with open(f"{self.model_dir}/scaler.pkl", "rb") as f:
                    self.scaler = pickle.load(f)
                
                # Load XGBoost
                self.xgb = XGBRegressor()
                self.xgb.load_model(f"{self.model_dir}/xgb_model.json")
                
                # Load LightGBM
                self.lgbm = lgb.Booster(model_file=f"{self.model_dir}/lgbm_model.txt")
                
                self.models_loaded = True
                print("✓ Pre-trained models loaded successfully")
            else:
                print("⚠ Pre-trained models not found. Will train on demand.")
                
        except Exception as e:
            print(f"⚠ Could not load pre-trained models: {e}")
            self.models_loaded = False
    
    def train_sarima(self, data: np.ndarray) -> Optional[any]:
        """Train SARIMA model"""
        try:
            model = SARIMAX(data, order=(1, 1, 1), seasonal_order=(0, 0, 0, 0))
            fitted = model.fit(disp=False)
            return fitted
        except Exception as e:
            print(f"SARIMA training error: {e}")
            return None
    
    def train_lstm(self, data: np.ndarray, window_size: int = 5) -> Tuple[Optional[any], Optional[any]]:
        """Train LSTM model"""
        try:
            from tensorflow.keras.models import Sequential
            from tensorflow.keras.layers import LSTM, Dense
            
            if len(data) <= window_size:
                return None, None
            
            scaler = MinMaxScaler()
            scaled_data = scaler.fit_transform(data.reshape(-1, 1))
            
            X, y = [], []
            for i in range(len(scaled_data) - window_size):
                X.append(scaled_data[i:i + window_size])
                y.append(scaled_data[i + window_size])
            X, y = np.array(X), np.array(y)
            
            model = Sequential([
                LSTM(50, activation='relu', input_shape=(window_size, 1)),
                Dense(1)
            ])
            model.compile(optimizer='adam', loss='mse')
            model.fit(X, y, epochs=10, verbose=0)
            
            return model, scaler
        except Exception as e:
            print(f"LSTM training error: {e}")
            return None, None
    
    def train_xgboost(self, data: np.ndarray, window_size: int = 5) -> Optional[any]:
        """Train XGBoost model"""
        try:
            if len(data) <= window_size:
                return None
            
            X = np.array([data[i:i + window_size] for i in range(len(data) - window_size)])
            y = np.array([data[i + window_size] for i in range(len(data) - window_size)])
            
            model = XGBRegressor(n_estimators=50, random_state=42)
            model.fit(X, y)
            return model
        except Exception as e:
            print(f"XGBoost training error: {e}")
            return None
    
    def train_lightgbm(self, data: np.ndarray, window_size: int = 5) -> Optional[any]:
        """Train LightGBM model"""
        try:
            if len(data) <= window_size:
                return None
            
            X = np.array([data[i:i + window_size] for i in range(len(data) - window_size)])
            y = np.array([data[i + window_size] for i in range(len(data) - window_size)])
            
            train_set = lgb.Dataset(X, label=y)
            params = {'objective': 'regression', 'metric': 'rmse', 'verbose': -1}
            model = lgb.train(params, train_set, num_boost_round=50)
            return model
        except Exception as e:
            print(f"LightGBM training error: {e}")
            return None
    
    def train_prophet(self, data: np.ndarray, dates: Optional[List[str]] = None) -> Optional[any]:
        """Train Prophet model"""
        try:
            # Create dataframe for Prophet
            if dates is None:
                dates = pd.date_range(start='2024-01-01', periods=len(data), freq='D')
            
            df = pd.DataFrame({
                'ds': dates,
                'y': data
            })
            
            model = Prophet(daily_seasonality=True, yearly_seasonality=True)
            model.fit(df)
            return model
        except Exception as e:
            print(f"Prophet training error: {e}")
            return None
    
    def predict_sarima(self, model: any, horizon: int) -> List[float]:
        """Generate SARIMA forecast"""
        try:
            forecast = model.forecast(steps=horizon)
            return forecast.tolist()
        except:
            return []
    
    def predict_lstm(self, model: any, scaler: any, recent_data: np.ndarray, horizon: int) -> List[float]:
        """Generate LSTM forecast"""
        try:
            predictions = []
            current_data = recent_data[-5:].copy()
            
            for _ in range(horizon):
                scaled = scaler.transform(current_data.reshape(-1, 1)).reshape(1, 5, 1)
                pred_scaled = model.predict(scaled, verbose=0)
                pred = scaler.inverse_transform(pred_scaled)[0][0]
                predictions.append(float(pred))
                
                # Update window
                current_data = np.append(current_data[1:], pred)
            
            return predictions
        except:
            return []
    
    def predict_xgboost(self, model: any, recent_data: np.ndarray, horizon: int) -> List[float]:
        """Generate XGBoost forecast"""
        try:
            predictions = []
            current_data = recent_data[-5:].copy()
            
            for _ in range(horizon):
                pred = model.predict(current_data.reshape(1, -1))[0]
                predictions.append(float(pred))
                current_data = np.append(current_data[1:], pred)
            
            return predictions
        except:
            return []
    
    def predict_lightgbm(self, model: any, recent_data: np.ndarray, horizon: int) -> List[float]:
        """Generate LightGBM forecast"""
        try:
            predictions = []
            current_data = recent_data[-5:].copy()
            
            for _ in range(horizon):
                pred = model.predict(current_data.reshape(1, -1))[0]
                predictions.append(float(pred))
                current_data = np.append(current_data[1:], pred)
            
            return predictions
        except:
            return []
    
    def predict_prophet(self, model: any, horizon: int) -> List[float]:
        """Generate Prophet forecast"""
        try:
            future = model.make_future_dataframe(periods=horizon)
            forecast = model.predict(future)
            return forecast['yhat'].tail(horizon).tolist()
        except:
            return []
