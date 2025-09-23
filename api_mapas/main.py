
import pandas as pd
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI
from pymongo import MongoClient
import uvicorn
from dotenv import load_dotenv
import os

from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager

""""

python main.py

"
"""


load_dotenv()

DB_URL = os.getenv("DB_URL")


app = FastAPI(title="API de Tickets Eléctricos")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create MongoDB client
    app.mongodb_client = AsyncIOMotorClient(DB_URL)
    app.mongodb = app.mongodb_client["Prueba1"]
    print("MongoDB connected")
    
    yield  # FastAPI runs here
    
    # Shutdown: close MongoDB client
    app.mongodb_client.close()
    print("MongoDB connection closed")



async def leer_ev():
    """ lee ev pasa a df limpio"""
    client = MongoClient(DB_URL)
    db = client["Prueba1"]
    collection = db["electrico"]
    docs=collection.find({})
    data_ev = pd.DataFrame(docs)
    

    estacion_df = pd.json_normalize(data_ev["estacion"])
    data_ev = data_ev.drop(columns=["estacion"]).join(estacion_df.add_prefix("estacion."))
    df_exploded = data_ev.explode("lineas").reset_index(drop=True)
    # Normaliza la columna "lineas" (dict → columnas)
    lineas_normalizadas = pd.json_normalize(df_exploded["lineas"])
    # Une las nuevas columnas con el dataset original
    data_ev = df_exploded.drop(columns=["lineas"]).join(lineas_normalizadas.add_prefix("lineas."))
    data_ev["fechaEmision"]=pd.to_datetime(data_ev["fechaEmision"])
    data_ev["horaEmision"]=pd.to_datetime(data_ev["horaEmision"], format="%H:%M:%S")
    return data_ev



@app.get("/mapakwh")
async def mapakwh():
    """ devuelve la localizacion de donde meter el heatmap  kwh en formato json"""
    data_ev = await leer_ev()
    df_map = data_ev.groupby(['estacion.lat', 'estacion.lon'])['lineas.kwh'].mean().reset_index()


    # Crear mapa centrado (ejemplo: centro de España)
    

    # Preparar datos para el HeatMap (lat, lon, peso)
    heat_data = [[row['estacion.lat'], row['estacion.lon'], row['lineas.kwh']] for index, row in df_map.iterrows()]

    # Añadir capa HeatMap
    
    return heat_data




@app.get("/tickets")
async def get_tickets():
    """Devuelve en dictinario los tickects ev"""

    df = await leer_ev()
    return df.to_dict(orient="records")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",       # archivo:instancia de FastAPI
        host="0.0.0.0",   # accesible desde otras máquinas
        port=8000,        # puerto de la API
        reload=True       # recarga automática al cambiar código
    )


