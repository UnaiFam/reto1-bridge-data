# READ ME
# **WIP**
USa python 3.12.11 
Se utilizo conda para gestion

Mirar requirements.txt para librerioas

Ahora esta funcipnando con  [render](https://reto1-bridge-data.onrender.com).

Si se usa el URL puede tardar en ponerse en marcha. Dara error pero si añades /docs al url veras la documentaciosn 
Detrodas formas esta en [este enlade](https://reto1-bridge-data.onrender.com/docs)

Tambien tended cuidado:
Cada vez que algien sube a main la API se reinicia. Esto puede petar la API y gastar los  500 min grtis que tenemos. Asegurarse de que las funciones funciones en local antes de commit en main. No se si se reinica por cada cambio solo por los cambios que le a la API.

Por cierto que alguien ponga plotly en requierements.txt que me he dado cuenta que no esta.




deberia de  borrar el .env y poner el gitnore pero que se va a hacer..., me da miedo ponerlo ahora que la API funciona en render a pesar que le he puesto que use el URL en render.

DB_URL=mongodb+srv://unaifam_db_user:4xcFf~_D3)qeR4C@cluster0.qdcfbed.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
DB_NAME=Prueba1

DB_NAME no se usa. Se que no deberia de la url de la base de datos aqui pero quiero assegurarme que el que lo lea le funcione.

Ahora mismo  corre en render

## run local
decir  las palabras magicas:

python main.py

DENTRO DE LA CARPETA  

y revisasr el localhost 8000 docs para ver la documetacion 

## Como funcioan 

* cuando se enciede lee la base de datos (sacado del ejemplo de mongodb aunque luego no lo usa)

* leer gas peaje, ev: lee base de datos y pasa a df limpio

* kwh: llama leerev y devuelve las coordenadas de un mapa de kwh medio por gasolinera.
    **ATENCION**: Ahora mismo solo duevuelve la localizacion de los puntos no devuelve un heatmap

resto de kpi
* mi idea es usar plotly para hacer graficas predeterminadas ejecutarlas aqui y luego usar .tojson() a la figura para que full lo lea  y hagan lo que tengan que hacer

## Imagen WIP

Yo estaba haciendo esto pero creo no me funciona:
 docker build -t mi_app:1.0 .
 reto1-bridge-data/api_mapas

## contraseñas inutiles
 tictackontrack@gmail.com

tlcTR4CK!.

database user

tictadmin

password 

tictacdmin