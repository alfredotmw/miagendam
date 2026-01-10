from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World", "Status": "Debug Mode Active"}

@app.get("/health")
def read_health():
    return {"status": "ok", "version": "probe_v1"}

@app.get("/env")
def read_env():
    # CAREFUL: Don't expose sensitive vars
    return {
        "python": "ok",
        "has_pandas": False
    }
