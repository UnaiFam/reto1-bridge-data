
import pandas as pd
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI
from pymongo import MongoClient
""""python "API MAPAS"/main.py"
"""


"""
tictackontrack@gmail.com

tlcTR4CK!.

database user

tictadmin

password 

tictacdmin


"""

app = FastAPI(title="API de Tickets Eléctricos")

@app.on_event("startup")
async def startup_db_client():
    app.mongodb_client = AsyncIOMotorClient("mongodb+srv://unaifam_db_user:4xcFf~_D3)qeR4C@cluster0.qdcfbed.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    app.mongodb = app.mongodb_client["Prueba1"]

# Cierre de conexión al apagar la app
@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()



async def leer_ev():
    collection = app.mongodb["electrico"]
    cursor = collection.find({})
    docs = await cursor.to_list(length=1000)
    df = pd.DataFrame(docs)

    # Normalizar 'estacion'
    estacion_df = pd.json_normalize(df["estacion"])
    df = df.drop(columns=["estacion"]).join(estacion_df.add_prefix("estacion."))

    # Explode 'lineas'
    df = df.explode("lineas").reset_index(drop=True)
    lineas_normalizadas = pd.json_normalize(df["lineas"])
    df = df.drop(columns=["lineas"]).join(lineas_normalizadas.add_prefix("lineas."))

    # Fechas
    df["fechaEmision"] = pd.to_datetime(df["fechaEmision"])
    df["horaEmision"] = pd.to_datetime(df["horaEmision"], format="%H:%M:%S")

    return df







@app.get("/mapakwh")
async def mapakwh():
    data_ev = await leer_ev()
    df_map = data_ev.groupby(['estacion.lat', 'estacion.lon'])['lineas.kwh'].mean().reset_index()


    # Crear mapa centrado (ejemplo: centro de España)
    

    # Preparar datos para el HeatMap (lat, lon, peso)
    heat_data = [[row['estacion.lat'], row['estacion.lon'], row['lineas.kwh']] for index, row in df_map.iterrows()]

    # Añadir capa HeatMap
    

    return heat_data




@app.get("/tickets")
async def get_tickets():
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


