from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from pydantic import BaseModel
import pandas as pd
import torch
from chronos import BaseChronosPipeline
import os

# Inicializar la aplicación FastAPI
app = FastAPI()

# Cargar el modelo al iniciar el servidor
@app.on_event("startup")
def load_model():
    global pipeline
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        raise RuntimeError("HF_TOKEN no está configurado en las variables de entorno")
    
    pipeline = BaseChronosPipeline.from_pretrained(
        "amazon/chronos-bolt-base",
        device_map="cpu",
        torch_dtype=torch.bfloat16,
        use_auth_token=hf_token
    )

@app.post("/forecast/")
async def forecast(
    file: UploadFile = File(...),
    prediction_length: int = Form(...),
    target_column: str = Form(...)
):
    # Validar entrada
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un CSV")
    
    # Leer el archivo CSV
    try:
        df = pd.read_csv(file.file)
        if target_column not in df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"El CSV debe contener una columna llamada '{target_column}'"
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error procesando el archivo: {e}")
    
    # Validar que prediction_length sea positivo
    if prediction_length <= 0:
        raise HTTPException(status_code=400, detail="prediction_length debe ser mayor a 0")
    
    # Preparar el contexto para el modelo
    try:
        context = torch.tensor(df[target_column].values, dtype=torch.float32)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error procesando la columna objetivo: {e}")
    
    # Generar el pronóstico
    forecast = pipeline.predict(context=context, prediction_length=prediction_length)
    
    # Extraer las desviaciones estándar de los cuantiles
    quantiles = [0.1, 0.9]
    quantile_indices = [int(q * forecast.shape[1]) for q in quantiles]
    lower_quantile = forecast[0, quantile_indices[0], :].cpu().numpy()
    upper_quantile = forecast[0, quantile_indices[1], :].cpu().numpy()

    # Obtener la mediana del pronóstico
    median_quantile_index = forecast.shape[1] // 2
    median_forecast = forecast[0, median_quantile_index, :].cpu().numpy()
    
    # Generar datos para la respuesta
    forecast_horizon = list(range(len(df[target_column]), len(df[target_column]) + len(median_forecast)))
    actual_data = df[target_column].tolist()
    
    return {
        "actual": actual_data,
        "forecast": median_forecast.tolist(),
        "horizon": forecast_horizon,
        "lower_quantile": lower_quantile.tolist(),
        "upper_quantile": upper_quantile.tolist()
    }