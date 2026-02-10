"""Training service for background model retraining"""
import numpy as np
import pandas as pd
import uuid
from typing import Dict, Any, List
from datetime import datetime

from models.forecasting_models import ForecastingModels
from utils.model_evaluator import ModelEvaluator
from utils.background_tasks import task_manager, TaskStatus


class TrainingService:
    """Handles background model training"""
    
    def __init__(self):
        self.models = ForecastingModels()
        self.evaluator = ModelEvaluator()
    
    def start_training_job(self, data: np.ndarray, dataset_id: str = None) -> str:
        """Start a background training job"""
        job_id = str(uuid.uuid4())
        
        # Create task
        task_manager.create_task(job_id, "model_training")
        
        # In a real async setup, this would be a background task
        # For now, we'll run it synchronously but track status
        task_manager.update_status(job_id, TaskStatus.PROCESSING)
        
        try:
            result = self.train_and_evaluate(data, dataset_id)
            task_manager.update_status(job_id, TaskStatus.COMPLETED, result=result)
        except Exception as e:
            task_manager.update_status(job_id, TaskStatus.FAILED, error=str(e))
        
        return job_id
    
    def train_and_evaluate(self, data: np.ndarray, dataset_id: str = None) -> Dict[str, Any]:
        """Train all models and evaluate performance"""
        print(f"Starting training on {len(data)} data points...")
        
        # Split data for validation
        split_idx = int(len(data) * 0.8)
        train_data = data[:split_idx]
        val_data = data[split_idx:]
        
        model_results = {}
        trained_models = {}
        
        # Train SARIMA
        try:
            print("Training SARIMA...")
            sarima = self.models.train_sarima(train_data)
            if sarima:
                preds = self.models.predict_sarima(sarima, len(val_data))
                if preds:
                    metrics = self.evaluator.evaluate_model(val_data, np.array(preds))
                    model_results["sarima"] = metrics
                    trained_models["sarima"] = sarima
                    print(f"✓ SARIMA: MAPE={metrics['mape']:.2f}%, RMSE={metrics['rmse']:.2f}")
        except Exception as e:
            print(f"✗ SARIMA failed: {e}")
        
        # Train LSTM
        try:
            print("Training LSTM...")
            lstm, scaler = self.models.train_lstm(train_data)
            if lstm and scaler:
                preds = self.models.predict_lstm(lstm, scaler, train_data, len(val_data))
                if preds:
                    metrics = self.evaluator.evaluate_model(val_data, np.array(preds))
                    model_results["lstm"] = metrics
                    trained_models["lstm"] = {"model": lstm, "scaler": scaler}
                    print(f"✓ LSTM: MAPE={metrics['mape']:.2f}%, RMSE={metrics['rmse']:.2f}")
        except Exception as e:
            print(f"✗ LSTM failed: {e}")
        
        # Train XGBoost
        try:
            print("Training XGBoost...")
            xgb = self.models.train_xgboost(train_data)
            if xgb:
                preds = self.models.predict_xgboost(xgb, train_data, len(val_data))
                if preds:
                    metrics = self.evaluator.evaluate_model(val_data, np.array(preds))
                    model_results["xgboost"] = metrics
                    trained_models["xgboost"] = xgb
                    print(f"✓ XGBoost: MAPE={metrics['mape']:.2f}%, RMSE={metrics['rmse']:.2f}")
        except Exception as e:
            print(f"✗ XGBoost failed: {e}")
        
        # Train LightGBM
        try:
            print("Training LightGBM...")
            lgbm = self.models.train_lightgbm(train_data)
            if lgbm:
                preds = self.models.predict_lightgbm(lgbm, train_data, len(val_data))
                if preds:
                    metrics = self.evaluator.evaluate_model(val_data, np.array(preds))
                    model_results["lightgbm"] = metrics
                    trained_models["lightgbm"] = lgbm
                    print(f"✓ LightGBM: MAPE={metrics['mape']:.2f}%, RMSE={metrics['rmse']:.2f}")
        except Exception as e:
            print(f"✗ LightGBM failed: {e}")
        
        # Train Prophet
        try:
            print("Training Prophet...")
            prophet = self.models.train_prophet(train_data)
            if prophet:
                preds = self.models.predict_prophet(prophet, len(val_data))
                if preds:
                    metrics = self.evaluator.evaluate_model(val_data, np.array(preds))
                    model_results["prophet"] = metrics
                    trained_models["prophet"] = prophet
                    print(f"✓ Prophet: MAPE={metrics['mape']:.2f}%, RMSE={metrics['rmse']:.2f}")
        except Exception as e:
            print(f"✗ Prophet failed: {e}")
        
        # Select best model
        best_model, best_metrics = self.evaluator.select_best_model(model_results)
        
        print(f"\n✓ Training complete. Best model: {best_model} (MAPE: {best_metrics.get('mape', 0):.2f}%)")
        
        return {
            "dataset_id": dataset_id,
            "model_results": model_results,
            "best_model": best_model,
            "best_metrics": best_metrics,
            "models_trained": len(model_results),
            "completed_at": datetime.utcnow().isoformat()
        }
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of a training job"""
        task = task_manager.get_task_status(job_id)
        
        if not task:
            return {
                "success": False,
                "error": "Job not found"
            }
        
        return {
            "success": True,
            "job_id": job_id,
            "status": task["status"],
            "created_at": task["created_at"].isoformat() if task.get("created_at") else None,
            "started_at": task["started_at"].isoformat() if task.get("started_at") else None,
            "completed_at": task["completed_at"].isoformat() if task.get("completed_at") else None,
            "result": task.get("result"),
            "error": task.get("error")
        }
