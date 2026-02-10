"""Forecast service - Core forecasting logic with auto model selection"""
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from models.forecasting_models import ForecastingModels, EnsembleResult
from models.db_models import ModelType, ForecastRequest
from utils.model_evaluator import ModelEvaluator
from services.llm_service import LLMService


class ForecastService:
    """Core forecasting service with auto model selection"""
    
    def __init__(self):
        self.models = ForecastingModels()
        self.evaluator = ModelEvaluator()
        self.llm_service = LLMService()
        
        # Try to load pre-trained models
        self.models.load_pretrained_models()
    
    def train_all_models(self, data: np.ndarray) -> Dict[str, Any]:
        """Train all available models on the data"""
        trained_models = {}
        
        print(f"Training models on {len(data)} data points...")
        
        # SARIMA
        sarima = self.models.train_sarima(data)
        if sarima:
            trained_models["sarima"] = sarima
            print("✓ SARIMA trained")
        
        # LSTM
        lstm, scaler = self.models.train_lstm(data)
        if lstm and scaler:
            trained_models["lstm"] = {"model": lstm, "scaler": scaler}
            print("✓ LSTM trained")
        
        # XGBoost
        xgb = self.models.train_xgboost(data)
        if xgb:
            trained_models["xgboost"] = xgb
            print("✓ XGBoost trained")
        
        # LightGBM
        lgbm = self.models.train_lightgbm(data)
        if lgbm:
            trained_models["lightgbm"] = lgbm
            print("✓ LightGBM trained")
        
        # Prophet
        prophet = self.models.train_prophet(data)
        if prophet:
            trained_models["prophet"] = prophet
            print("✓ Prophet trained")
        
        return trained_models
    
    def generate_predictions(self, trained_models: Dict[str, Any], 
                           recent_data: np.ndarray, horizon: int) -> Dict[str, List[float]]:
        """Generate predictions from all trained models"""
        predictions = {}
        
        # SARIMA predictions
        if "sarima" in trained_models:
            preds = self.models.predict_sarima(trained_models["sarima"], horizon)
            if preds:
                predictions["sarima"] = preds
        
        # LSTM predictions
        if "lstm" in trained_models:
            lstm_data = trained_models["lstm"]
            preds = self.models.predict_lstm(
                lstm_data["model"], lstm_data["scaler"], recent_data, horizon
            )
            if preds:
                predictions["lstm"] = preds
        
        # XGBoost predictions
        if "xgboost" in trained_models:
            preds = self.models.predict_xgboost(trained_models["xgboost"], recent_data, horizon)
            if preds:
                predictions["xgboost"] = preds
        
        # LightGBM predictions
        if "lightgbm" in trained_models:
            preds = self.models.predict_lightgbm(trained_models["lightgbm"], recent_data, horizon)
            if preds:
                predictions["lightgbm"] = preds
        
        # Prophet predictions
        if "prophet" in trained_models:
            preds = self.models.predict_prophet(trained_models["prophet"], horizon)
            if preds:
                predictions["prophet"] = preds
        
        return predictions
    
    def evaluate_models(self, predictions: Dict[str, List[float]], 
                       actual: np.ndarray) -> Dict[str, Dict[str, float]]:
        """Evaluate all model predictions against actual values"""
        results = {}
        
        for model_name, preds in predictions.items():
            # Use last N actual values for evaluation
            n = min(len(preds), len(actual))
            if n > 0:
                actual_subset = actual[-n:]
                pred_subset = np.array(preds[:n])
                
                metrics = self.evaluator.evaluate_model(actual_subset, pred_subset)
                results[model_name] = metrics
        
        return results
    
    def forecast_demand(self, request: ForecastRequest) -> Dict[str, Any]:
        """Main demand forecasting method"""
        try:
            # Extract data
            if request.data:
                data = np.array(request.data)
            else:
                raise ValueError("No data provided for forecasting")
            
            if len(data) < 10:
                raise ValueError("Insufficient data for forecasting (minimum 10 points required)")
            
            # If specific model requested (not auto)
            if request.model != ModelType.AUTO:
                return self._forecast_single_model(data, request)
            
            # Auto mode: train all models and select best
            return self._forecast_auto_mode(data, request)
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _forecast_single_model(self, data: np.ndarray, request: ForecastRequest) -> Dict[str, Any]:
        """Forecast using a single specified model"""
        model_name = request.model.value
        horizon = request.horizon
        
        # Train the requested model
        if model_name == "sarima":
            model = self.models.train_sarima(data)
            predictions = self.models.predict_sarima(model, horizon) if model else []
        elif model_name == "lstm":
            model, scaler = self.models.train_lstm(data)
            predictions = self.models.predict_lstm(model, scaler, data, horizon) if model else []
        elif model_name == "xgboost":
            model = self.models.train_xgboost(data)
            predictions = self.models.predict_xgboost(model, data, horizon) if model else []
        elif model_name == "lightgbm":
            model = self.models.train_lightgbm(data)
            predictions = self.models.predict_lightgbm(model, data, horizon) if model else []
        elif model_name == "prophet":
            model = self.models.train_prophet(data)
            predictions = self.models.predict_prophet(model, horizon) if model else []
        else:
            predictions = []
        
        if not predictions:
            return {
                "success": False,
                "error": f"Failed to generate predictions with {model_name}"
            }
        
        # Calculate confidence intervals
        confidence_intervals = self.evaluator.calculate_confidence_interval(
            predictions, request.confidence_level
        )
        
        # Generate LLM explanation
        forecast_data = {
            "predictions": predictions,
            "model_used": model_name,
            "metrics": {},
            "confidence_intervals": confidence_intervals
        }
        
        llm_explanation = self.llm_service.explain_forecast(forecast_data, request.use_claude)
        
        return {
            "success": True,
            "forecast_id": str(uuid.uuid4()),
            "model_used": model_name,
            "predictions": predictions,
            "confidence_intervals": confidence_intervals,
            "metrics": {},
            "feature_importance": [],
            "llm_explanation": llm_explanation,
            "llm_used": "claude" if request.use_claude else "ollama",
            "created_at": datetime.utcnow().isoformat()
        }
    
    def _forecast_auto_mode(self, data: np.ndarray, request: ForecastRequest) -> Dict[str, Any]:
        """Auto mode: train all models and select best based on validation"""
        horizon = request.horizon
        
        # Split data: use last 20% for validation
        split_idx = int(len(data) * 0.8)
        train_data = data[:split_idx]
        val_data = data[split_idx:]
        
        # Train all models
        trained_models = self.train_all_models(train_data)
        
        if not trained_models:
            return {
                "success": False,
                "error": "Failed to train any models"
            }
        
        # Generate validation predictions
        val_horizon = len(val_data)
        val_predictions = self.generate_predictions(trained_models, train_data, val_horizon)
        
        # Evaluate models
        model_results = self.evaluate_models(val_predictions, val_data)
        
        # Select best model
        best_model_name, best_metrics = self.evaluator.select_best_model(model_results)
        
        print(f"✓ Best model selected: {best_model_name} (MAPE: {best_metrics.get('mape', 0):.2f}%)")
        
        # Generate final forecast with best model
        final_predictions = self.generate_predictions(trained_models, data, horizon)
        best_predictions = final_predictions.get(best_model_name, [])
        
        if not best_predictions:
            # Fallback to any available predictions
            best_model_name = list(final_predictions.keys())[0]
            best_predictions = final_predictions[best_model_name]
        
        # Calculate confidence intervals
        confidence_intervals = self.evaluator.calculate_confidence_interval(
            best_predictions, request.confidence_level
        )
        
        # Generate LLM explanation
        forecast_data = {
            "predictions": best_predictions,
            "model_used": best_model_name,
            "metrics": best_metrics,
            "confidence_intervals": confidence_intervals,
            "all_model_results": model_results
        }
        
        llm_explanation = self.llm_service.explain_forecast(forecast_data, request.use_claude)
        
        return {
            "success": True,
            "forecast_id": str(uuid.uuid4()),
            "model_used": best_model_name,
            "predictions": best_predictions,
            "confidence_intervals": confidence_intervals,
            "metrics": best_metrics,
            "all_model_results": model_results,
            "model_breakdown": {name: preds for name, preds in final_predictions.items()},
            "feature_importance": [],
            "llm_explanation": llm_explanation,
            "llm_used": "claude" if request.use_claude else "ollama",
            "created_at": datetime.utcnow().isoformat()
        }
