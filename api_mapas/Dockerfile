<<<<<<< HEAD
FROM python:3.12.11

# Crear directorio de trabajo
# docker build -t mi_app:1.0 .

# Copiar dependencias
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de la app
COPY main.py .
COPY .env .

# Exponer puerto
EXPOSE 6000

# Arrancar servidor
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "6000"]
=======
FROM python:3.12.11

# Crear directorio de trabajo
# docker build -t mi_app:1.0 .

# Copiar dependencias
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de la app
COPY main.py .
COPY .env .

# Exponer puerto
EXPOSE 9000

# Arrancar servidor
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]
>>>>>>> 5ed84a8f0dab3f8fd421d3f6d403f781b6afd584
CMD ["python", "main.py"]