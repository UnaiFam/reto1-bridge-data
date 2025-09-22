from fastapi import FastAPI, UploadFile, File
from llama_cloud_services import LlamaExtract
from llama_cloud_services import SourceText

from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="OCR")

api_key = os.getenv("LLAMA-API-KEY")
agent_name = os.getenv("NOMBRE-AGENTE")
extractor = LlamaExtract(api_key=api_key)
agent = extractor.get_agent(name=agent_name)

@app.post("/extract/")
async def extract_data(file: UploadFile = File(...)):

    file_bytes = await file.read()
    filename=file.filename
    # Si agent.extract acepta bytes:
    result = agent.extract(SourceText(file=file_bytes, filename=filename))
    #(file_bytes)
    return {"data": result.data}