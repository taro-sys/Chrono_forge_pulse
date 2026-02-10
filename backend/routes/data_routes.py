"""Data management API routes"""
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from typing import Dict, Any, List
import pandas as pd
import io
import json
import uuid
from datetime import datetime
import numpy as np

from services.training_service import TrainingService

router = APIRouter(prefix="/api/data", tags=["data"])

# Initialize service
training_service = TrainingService()

# In-memory storage for uploaded datasets (in production, use MongoDB)
datasets_store = {}


@router.post("/upload")
async def upload_data(file: UploadFile = File(...), 
                     auto_train: bool = True,
                     background_tasks: BackgroundTasks = None) -> Dict[str, Any]:
    """
    Upload sales data (CSV or JSON) and optionally trigger auto-retraining
    
    - **file**: CSV or JSON file with sales data
    - **auto_train**: Automatically retrain models on upload (default: True)
    """
    try:
        # Read file content
        contents = await file.read()
        
        # Determine file type and parse
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith('.json'):
            data = json.loads(contents)
            df = pd.DataFrame(data)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Use CSV or JSON.")
        
        # Extract sales values
        if 'sales_value' in df.columns:
            sales_data = df['sales_value'].values
        elif len(df.columns) > 1:
            # Use second column as sales data
            sales_data = df[df.columns[1]].values
        else:
            raise HTTPException(status_code=400, detail="Could not find sales data column")
        
        # Convert to float
        sales_data = sales_data.astype(float)
        
        # Generate dataset ID
        dataset_id = str(uuid.uuid4())
        
        # Store dataset
        datasets_store[dataset_id] = {
            "id": dataset_id,
            "name": file.filename,
            "data": sales_data.tolist(),
            "uploaded_at": datetime.utcnow().isoformat(),
            "record_count": len(sales_data)
        }
        
        response = {
            "success": True,
            "dataset_id": dataset_id,
            "filename": file.filename,
            "records_imported": len(sales_data),
            "uploaded_at": datetime.utcnow().isoformat()
        }
        
        # Trigger background training if requested
        if auto_train and len(sales_data) >= 10:
            job_id = training_service.start_training_job(sales_data, dataset_id)
            response["training_job_id"] = job_id
            response["status"] = "processing"
        else:
            response["status"] = "uploaded"
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets")
async def list_datasets() -> Dict[str, Any]:
    """
    List all uploaded datasets
    """
    datasets = [
        {
            "id": ds["id"],
            "name": ds["name"],
            "record_count": ds["record_count"],
            "uploaded_at": ds["uploaded_at"]
        }
        for ds in datasets_store.values()
    ]
    
    return {
        "success": True,
        "datasets": datasets,
        "total_count": len(datasets)
    }


@router.get("/datasets/{dataset_id}")
async def get_dataset(dataset_id: str) -> Dict[str, Any]:
    """
    Get dataset by ID
    """
    if dataset_id not in datasets_store:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    return {
        "success": True,
        "dataset": datasets_store[dataset_id]
    }


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(dataset_id: str) -> Dict[str, Any]:
    """
    Delete dataset by ID
    """
    if dataset_id not in datasets_store:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    del datasets_store[dataset_id]
    
    return {
        "success": True,
        "message": "Dataset deleted successfully"
    }


@router.post("/train")
async def trigger_training(dataset_id: str = None, data: List[float] = None) -> Dict[str, Any]:
    """
    Manually trigger model training
    
    - **dataset_id**: ID of uploaded dataset
    - **data**: Or provide data directly
    """
    try:
        # Get data
        if dataset_id:
            if dataset_id not in datasets_store:
                raise HTTPException(status_code=404, detail="Dataset not found")
            train_data = np.array(datasets_store[dataset_id]["data"])
        elif data:
            train_data = np.array(data)
        else:
            raise HTTPException(status_code=400, detail="Provide either dataset_id or data")
        
        if len(train_data) < 10:
            raise HTTPException(status_code=400, detail="Insufficient data for training (minimum 10 points)")
        
        # Start training job
        job_id = training_service.start_training_job(train_data, dataset_id)
        
        return {
            "success": True,
            "job_id": job_id,
            "status": "processing",
            "message": "Training job started"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/train/status/{job_id}")
async def get_training_status(job_id: str) -> Dict[str, Any]:
    """
    Get status of a training job
    """
    result = training_service.get_job_status(job_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Job not found"))
    
    return result


@router.get("/statistics")
async def get_statistics() -> Dict[str, Any]:
    """
    Get statistics about uploaded data
    """
    try:
        if not datasets_store:
            return {
                "success": True,
                "total_datasets": 0,
                "total_records": 0
            }
        
        total_records = sum(ds["record_count"] for ds in datasets_store.values())
        
        # Calculate aggregate statistics
        all_data = []
        for ds in datasets_store.values():
            all_data.extend(ds["data"])
        
        if all_data:
            stats = {
                "success": True,
                "total_datasets": len(datasets_store),
                "total_records": total_records,
                "min_value": float(min(all_data)),
                "max_value": float(max(all_data)),
                "mean_value": float(np.mean(all_data)),
                "std_value": float(np.std(all_data))
            }
        else:
            stats = {
                "success": True,
                "total_datasets": len(datasets_store),
                "total_records": 0
            }
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
