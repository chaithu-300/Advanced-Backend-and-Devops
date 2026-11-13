from fastapi import FastAPI, HTTPException, Header, Body #pyright: ignore
import functions
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware #pyright: ignore
from datetime import date

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

@app.post("/add_packages")
def Register_packages(package_name: str, destination: str, weight: float, arrival_date: date, token = Header(None)):
    username = functions.verify_token(token=token)
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or Expired token")
    return functions.register_package(package_name,destination,weight,arrival_date)


@app.get("/packages/{package_id}")
def get_package_details(package_id: int, token = Header(None)):
    username = functions.verify_token(token=token)
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or Expired token")
    response = functions.get_package(package_id)

    if response is None:
        raise HTTPException(status_code=404,detail="Package not found")

    return response

@app.patch("/packages/{package_id}")
def Update_package(package_id: int, package_name = None, destination = None, weight = None, arrival_date = None, status = None, token = Header(None)):
    username = functions.verify_token(token=token)
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or Expired token")

    response = functions.update_package(
        package_id,
        package_name,
        destination,
        weight,
        arrival_date,
        status
    )

    if response is None:
        raise HTTPException(status_code=404, detail="Package not found")

    return response


@app.delete("/packages/{package_id}")
def Delete_package(package_id: int, token = Header(None)):
    username = functions.verify_token(token=token)
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or Expired token")

    result = functions.delete_package(package_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Package not found")

    if result == "cannot delete":
        raise HTTPException(status_code=400, detail="Cannot delete an assigned or dispatched package")

    return {"message": "Package deleted successfully"}


@app.get("/packages")
def get_packages(destination = None, arrival_date = None, status = None, token = Header(None)):
    username = functions.verify_token(token=token)
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or Expired token")

    packages = functions.search_by_filter(destination, arrival_date, status)

    return packages


@app.get("/dispatch-batches")
def get_dispatch_batches(destination=None, vehicle=None, status=None, token = Header(None)):
    username = functions.verify_token(token=token)
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or Expired token")

    batches = functions.search_dispatch_batches(destination,vehicle,status)

    return batches

@app.get("/warehouse/statistics")
def warehouse_statistics(token = Header(None)):
    username = functions.verify_token(token=token)
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or Expired token")
    statistics = functions.get_warehouse_statistics()
    return statistics


@app.post("/dispatch-batches")
def create_dispatch_batch(
    destination: str = Body(),
    vehicle: str = Body(),
    package_ids: list[int] = Body(),
    token = Header(None)
):
    username = functions.verify_token(token=token)
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or Expired token")
    response = functions.create_dispatch_batch(
        destination,
        vehicle,
        package_ids
    )
    if response == "no packages provided":
        raise HTTPException(status_code=400, detail="At least one package is required")

    if response == "duplicate package IDs":
        raise HTTPException(status_code=400, detail="Duplicate package IDs are not allowed")

    if response == "package not found":
        raise HTTPException(status_code=404, detail="One or more packages not found")

    if response == "destination mismatch":
        raise HTTPException(status_code=400, detail="All packages must have the same destination as the batch")

    if response == "package already assigned or dispatched":
        raise HTTPException(status_code=400, detail="One or more packages are already assigned or dispatched")

    return response

@app.post("/login")
def login(username, password):
    token = functions.verify_login(username=username, password=password)
    if not token:
        raise HTTPException(status_code=401, detail = "Invalid Credentials")
    return {"token": token}

@app.post("/register")
def register_user(user_name = Body(), password = Body()):
    if functions.register_user(user_name=user_name, password=password):
        return {"message": "user registered successfully"}
    raise HTTPException(status_code = 400, detail = "user already exists")

@app.post("/refresh")
def refresh(refresh_token = Header(None)):
    username = functions.verify_token(token=refresh_token)
    if not username:
        raise HTTPException(status_code=401, detail = "Invalid or Expired refresh token")
    access_token = functions.create_token(username=username, token_type="access")
    return {"access_token": access_token}


