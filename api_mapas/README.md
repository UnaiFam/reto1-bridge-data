# READ ME
# **WIP**
USa python 3.12.11 
Se utilizo conda para gestion

Mirar requirements.txt para librerioas

Ahora esta funcipnando con  [render](https://reto1-bridge-data.onrender.com).

Si se usa el URL puede tardar en ponerse en marcha. Dara error pero si añades /docs al url veras la documentaciosn 
Detrodas formas esta en [este enlace](https://reto1-bridge-data.onrender.com/docs)

Tambien tended cuidado:
Cada vez que algien sube a main la API se reinicia. Esto puede petar la API y gastar los  500 min grtis que tenemos. Asegurarse de que las funciones funciones en local antes de commit en main. No se si se reinica por cada cambio solo por los cambios que le a la API.






deberia de  borrar el .env y poner el gitnore pero que se va a hacer..., me da miedo ponerlo ahora que la API funciona en render a pesar que le he puesto que use el URL en render.

DB_URL=mongodb+srv://<dbuser>:<dbpassword>@cluster0.qdcfbed.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
DB_NAME=DBmae

DB_NAME no se usa. Se que no deberia de la url de la base de datos aqui pero quiero assegurarme que el que lo lea le funcione.

Ahora mismo  corre en render

## run local
decir  las palabras magicas:

python main.py

DENTRO DE LA CARPETA  

y revisar el localhost 8000 docs para ver la documetacion 

## Como funcionan 

* cuando se enciede lee la base de datos (sacado del ejemplo de mongodb aunque luego no lo usa)

* leer gas peaje, ev: lee base de datos y pasa a df limpio

* **mapakwh:** 
    *por detras*
    llama a una funcion que llama a la base de datos electico pasa a dataframe y se filtra con pandas

    *Por delante*
    Devuelve para todos los medios
    Formato: [[lat, lon, precio_medio], ...] 
     
* **mapagas:** 
    *por detras*
    Actualmente la base de datos tiene


    llama a una funcion que llama a la base de datos electrico pasa a dataframe y se filtra con pandas

    *Por delante*
    Devuelve para todos los medios
    Formato: [[lat, lon, precio_medio], ...]


* **mapagas_concreto:** 
    *por detras*
    Mismo que 


    return heat_data
    llama a una funcion que llama a la base de datos electrico pasa a dataframe y se filtra con pandas
    Actualmente la base de datos tiene ['Gasóleo A', 'Gasolina 95 E5', 'Gasolina 98 E5', 'Gasóleo Premium']
    Si se quiere filtrar mas de uno ej. ['Gasolina 98 E5', 'Gasóleo Premium']
    *Por delante*
    Devuelve para todos los medios
    Formato: [[lat, lon, precio_medio], ...]
