from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World from Main", "Status": "Debug Mode Active"}

@app.get("/health")
def read_health():
    return {"status": "ok", "version": "probe_v2_main_override"}





