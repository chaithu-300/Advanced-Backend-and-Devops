from fastapi import FastAPI, HTTPException
import functions
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
@app.get("/")
def hello():
    return {"message": "Warehouse-Dispatch-Management running successfully"}

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://localhost:5174", "http://127.0.0.1:5174"],
    allow_methods = ["*"],
    allow_headers = ["*"],

)

@app.post("/packages")
def add_package(package):

    response = functions.register_package(package)

    return {
        "message": "Package registered successfully",
        "package": response
    }

@app.get("/packages/{package_id}")
def get_package_details(package_id: int):

    response = functions.get_package(package_id)

    if response is None:
        raise HTTPException(status_code=404,detail="Package not found")

    return response