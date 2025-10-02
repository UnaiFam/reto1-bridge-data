# Diseño de un Sistema de Reconocimiento Óptico de Caracteres, Almacenamiento y Construcción de una API como Parte del Desarrollo de una Aplicación Web Orientada al Análisis de Indicadores de Movilidad

**Autores:**  
Fernando Moro  
Jon Olalde  
Unai Famoso  
Zaven Velázquez  
Silvia Mencía

---

## Resumen

El equipo de Data Science diseñó e implementó un sistema de almacenamiento central y una API de consultas estadísticas predefinidas. Estos componentes permiten a otros módulos de la aplicación acceder de forma rápida y estandarizada a métricas relevantes como conteos, distribuciones y promedios.

---

## Introducción

El objetivo del proyecto ha sido crear una **aplicación web** que permitiese obtener información sobre el consumo de combustible y peajes en una flota de vehículos asociados a una empresa y para usuarios particulares. Además, se ofrecen a los usuarios de una manera **visual, sencilla y rápida** las estadísticas asociadas a dicha información.

La aplicación está formada por varios módulos:

1. **Recepción y digitalización de facturas y tickets**, provenientes del pago de repostajes de vehículos eléctricos, no eléctricos y peajes.  
2. **Almacenamiento**, dividido en dos sistemas:  
   - Uno para guardar el documento original.  
   - Otro para almacenar solo la información filtrada.  
3. **API de cálculo estadístico**, que explota la información almacenada y realiza cálculos.  
4. **Backend y Frontend**, que comunican los datos procesados y los muestran a los usuarios.

> El esquema general de la aplicación se muestra en la figura 1.

El equipo de Data Science definió el sistema OCR, diseñó el almacenamiento y construyó la API de estadísticas.

---

## Sistema Óptico de Reconocimiento de Caracteres (OCR)

La digitalización de la información contenida en las facturas y tickets se realizó mediante **APIs con modelos de computer vision preentrenados**. Se evaluaron dos enfoques:

### API de OCR Propia

- Construida con la librería [doctr](https://github.com/mindee/doctr) de Python y el framework **FastAPI**.  
- Endpoint que acepta documentos en PDF, JPEG o PNG y devuelve:
  - Un archivo JSON con la información extraída.  
  - Un valor de precisión del reconocimiento.  

> Finalmente, esta API fue descartada para el MVP debido a limitaciones de memoria en Render (servicio gratuito de despliegue).

📎 [Repositorio de la API OCR propia](https://github.com/UnaiFam/reto1-bridge-data/tree/main/app_OCR_doctr)

---

### API de Terceros

Dado que la API propia no se pudo desplegar gratuitamente, se optó por **utilizar la API de LlamaCloud®**, que ofrece un pipeline completo para:

- Ingestión de documentos en diferentes formatos.  
- Análisis, indexación, recuperación y extracción estructurada.  

Se configuraron los campos a extraer y se obtienen en JSON. Si algún campo no se puede extraer, aparece vacío.

Las consultas desde el backend a LlamaCloud se realizan a través de una **API intermedia construida con FastAPI** y desplegada en Render. Esta API tiene dos endpoints:

- Facturas de repostaje  
- Facturas de peaje

📎 [Repositorio API LlamaCloud](https://github.com/UnaiFam/reto1-bridge-data/tree/main/Llamacloud_ocr_api/Principal)  
📄 [Documentación en Google Docs](https://docs.google.com/document/d/1Sdy8kkyl08lz5qhChWvyyaHnNuHbEfTD0xk18BoxwYk/edit?usp=sharing)

---

## Sistema de Almacenamiento

Como sistema de almacenamiento analítico se utilizó **MongoDB**, una base de datos no relacional, para guardar los archivos JSON generados por la API de LlamaCloud.  

Se definieron **tres colecciones** en el mismo clúster para almacenar:

- Tickets de repostaje **no eléctrico**  
- Tickets de repostaje **eléctrico**  
- Tickets de **peajes**

La **gestión del flujo de archivos** desde el OCR hasta la base de datos fue implementada por el equipo full stack.

---

## API de Cálculo de Estadísticas

Para el módulo de estadísticas se construyó una **API con FastAPI** y se desplegó en Render.  

- Contiene diferentes endpoints que devuelven estadísticas en base a **KPIs definidos**.  
- Se conecta al clúster de MongoDB para obtener datos de facturas y tickets.  
- Devuelve resultados en **formato JSON** para el backend, que posteriormente son mostrados en el frontend.

📎 [Repositorio de la API de Estadísticas](https://github.com/UnaiFam/reto1-bridge-data/tree/main/API_estadistica)

---

## API de Mapas

Se desarrolló un prototipo de API que:

- Consulta una base de datos y devuelve **coordenadas + información** para representarlas en un mapa.  
- Cuenta con tres funciones actuales:
  - `mapakwh`
  - `mapagas`
  - `mapagas_concreto`

Formato de salida:  
```json
[
  [lat, lon, precio_medio],
  ...
]
```

📎 [Repositorio API Mapas](https://github.com/UnaiFam/reto1-bridge-data/tree/main/api_mapas)  
🌐 [Documentación interactiva de FastAPI](https://reto1-bridge-data.onrender.com/docs)

---

## Render

Tras desarrollar las tres APIs (OCR LlamaCloud, Estadísticas y Mapas):

1. Se **contenedorizó** cada API usando **Docker** para probar su correcto funcionamiento en entornos aislados.  
2. Se desplegaron en **Render**, un servicio en la nube que permite la orquestación y publicación de aplicaciones de forma escalable.  

> Esta etapa validó el despliegue en un entorno productivo y garantizó la disponibilidad de los servicios.

---

## Generación de Datos Sintéticos

Para generar datos sintéticos se aplicó un enfoque que combina **realismo geoespacial** y **consistencia temporal**:

1. Definición de una **cobertura realista de puntos y estaciones**, distribuidos según patrones geográficos verosímiles.  
2. Creación de **series históricas reproducibles** de precios, aplicando:
   - Offsets deterministas.  
   - Ruido controlado para variabilidad.  
3. Incorporación de **coherencia territorial**, integrando estructuras de peajes y zonas para asegurar relaciones espaciales consistentes.

📎 Generadores de datos sintéticos:  
- [Tickets eléctricos](https://github.com/UnaiFam/reto1-bridge-data/tree/main/Script_generador_tickets_sinteticos_electricos)  
- [Tickets gasolina](https://github.com/UnaiFam/reto1-bridge-data/tree/main/Script_generador_tickets_sinteticos_gasolina)

---

✅ **Proyecto desarrollado por el equipo de Data Science y Full Stack** como parte de un sistema integral para el análisis de indicadores de movilidad mediante OCR, almacenamiento estructurado y APIs estadísticas.
