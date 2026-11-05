from fastapi import FastAPI, HTTPException
import functions
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
@app.get("/")
def hello():
    return {"message": "Laundry-Hostel-Machines running successfully"}

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://localhost:5174", "http://127.0.0.1:5174"],
    allow_methods = ["*"],
    allow_headers = ["*"],
)

@app.post("/add_machine")
def add_machine(name, block, kind, cycles_minutes, in_service):
    return functions.add_machines(name, block, kind, cycles_minutes, in_service)

@app.get("/get_machines by id/{machine_id}")
def get_machines_by_id(machine_id):
    return functions.get_machines_by_id(machine_id)

@app.get("/get_all_machines/")
def get_all_machines(block= False, kind = False):
    return functions.get_machines(block, kind)

@app.patch("/update_machine/")
def update_machine(in_service, machine_id):
    return functions.update_machines(in_service, machine_id)

@app.get("/machines/attention")
def get_todays_usage_stats(block: str):
    if block not in ["a", "b", "c", "d"]:
        raise HTTPException(
            status_code=422, 
            detail="Block must be one of the following: a, b, c, d"
        )
    return functions.get_todays_usage(block)




