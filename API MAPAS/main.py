import follium
import pandas as pd
from fastapi import FastAPI
from pymongo import MongoClient

"""
tictackontrack@gmail.com

tlcTR4CK!.

database user

tictadmin

password 

tictacdmin


"""

client = MongoClient(connection_string)
app = FastAPI(title="Mapa")
data_ev=pd.read_json("Script_generador_tickets_sinteticos_electricos/data/tickets_ev_sinteticos.json")

estacion_df = pd.json_normalize(data_ev["estacion"])
data_ev = data_ev.drop(columns=["estacion"]).join(estacion_df.add_prefix("estacion."))



df_exploded = data_ev.explode("lineas").reset_index(drop=True)

# Normaliza la columna "lineas" (dict → columnas)
lineas_normalizadas = pd.json_normalize(df_exploded["lineas"])

# Une las nuevas columnas con el dataset original
data_ev = df_exploded.drop(columns=["lineas"]).join(lineas_normalizadas.add_prefix("lineas."))


data_ev["fechaEmision"]=pd.to_datetime(data_ev["fechaEmision"])

data_ev["horaEmision"]=pd.to_datetime(data_ev["horaEmision"], format="%H:%M:%S")


from follium.plugins import HeatMap

df_map = data_ev.groupby(['estacion.lat', 'estacion.lon'])['lineas.kwh'].sum().reset_index()


# Crear mapa centrado (ejemplo: centro de España)
m = follium.Map(location=[40.0, -3.7], zoom_start=6, tiles="CartoDB positron")

# Preparar datos para el HeatMap (lat, lon, peso)
heat_data = [[row['estacion.lat'], row['estacion.lon'], row['lineas.kwh']] for index, row in df_map.iterrows()]

# Añadir capa HeatMap
HeatMap(heat_data, radius=15, blur=10, max_zoom=1).add_to(m)

# Mostrar en Jupyter
m
