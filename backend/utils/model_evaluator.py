"""Model evaluation utilities for auto-selection"""
import numpy as np
from typing import List, Dict, Tuple


class ModelEvaluator:
    """Evaluate and compare forecasting models"""
    
    @staticmethod
    def calculate_mape(actual: np.ndarray, predicted: np.ndarray) -> float:
        """Calculate Mean Absolute Percentage Error"""
        try:
            # Avoid division by zero
            mask = actual != 0
            if not mask.any():
                return 100.0
            
            mape = np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100
            return float(mape)
        except:
            return 100.0
    
    @staticmethod
    def calculate_rmse(actual: np.ndarray, predicted: np.ndarray) -> float:
        """Calculate Root Mean Square Error"""
        try:
            rmse = np.sqrt(np.mean((actual - predicted) ** 2))
            return float(rmse)
        except:
            return float('inf')
    
    @staticmethod
    def calculate_mae(actual: np.ndarray, predicted: np.ndarray) -> float:
        """Calculate Mean Absolute Error"""
        try:
            mae = np.mean(np.abs(actual - predicted))
            return float(mae)
        except:
            return float('inf')
    
    @staticmethod
    def calculate_r2(actual: np.ndarray, predicted: np.ndarray) -> float:
        """Calculate R-squared score"""
        try:
            ss_res = np.sum((actual - predicted) ** 2)
            ss_tot = np.sum((actual - np.mean(actual)) ** 2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            return float(r2)
        except:
            return 0.0
    
    @staticmethod
    def evaluate_model(actual: np.ndarray, predicted: np.ndarray) -> Dict[str, float]:
        """Calculate all metrics for a model"""
        return {
            "mape": ModelEvaluator.calculate_mape(actual, predicted),
            "rmse": ModelEvaluator.calculate_rmse(actual, predicted),
            "mae": ModelEvaluator.calculate_mae(actual, predicted),
            "r2": ModelEvaluator.calculate_r2(actual, predicted)
        }
    
    @staticmethod
    def select_best_model(model_results: Dict[str, Dict[str, float]]) -> Tuple[str, Dict[str, float]]:
        """Select best model based on MAPE (lower is better)"""
        if not model_results:
            return "none", {}
        
        # Filter out models with no valid predictions
        valid_models = {
            name: metrics 
            for name, metrics in model_results.items() 
            if metrics.get("mape", 100) < 100
        }
        
        if not valid_models:
            # Return first available model as fallback
            first_model = list(model_results.keys())[0]
            return first_model, model_results[first_model]
        
        # Select model with lowest MAPE
        best_model = min(valid_models.items(), key=lambda x: x[1]["mape"])
        return best_model[0], best_model[1]
    
    @staticmethod
    def calculate_confidence_interval(predictions: List[float], 
                                     confidence_level: float = 0.95) -> Dict[str, List[float]]:
        """Calculate confidence intervals for predictions"""
        try:
            predictions_array = np.array(predictions)
            
            # Estimate standard deviation (simple method)
            std_dev = np.std(predictions_array) if len(predictions_array) > 1 else predictions_array[0] * 0.1
            
            # Z-score for confidence level
            z_scores = {
                0.90: 1.645,
                0.95: 1.96,
                0.99: 2.576
            }
            z = z_scores.get(confidence_level, 1.96)
            
            margin = z * std_dev
            
            lower = (predictions_array - margin).tolist()
            upper = (predictions_array + margin).tolist()
            
            return {
                "lower": lower,
                "upper": upper
            }
        except:
            return {
                "lower": predictions,
                "upper": predictions
            }
