from fastapi import FastAPI, HTTPException
import functions
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
@app.get("/")
def hello():
    return {"message": "Laundry-Hostel-Machines running successfully"}

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods = ["*"],
    allow_headers = ["*"],
)

@app.post("/add_machine")
def add_machine(name, block, kind, cycles_minutes, in_service):
    return functions.add_machines(name, block, kind, cycles_minutes, in_service)

@app.get("/machines_by_id/{machine_id}")
def get_single_machine_endpoint(machine_id):
    machine = functions.get_machine_by_id(machine_id)
    if machine is None:
        raise HTTPException(status_code = 404, detail = "Machine not found")
    return functions.get_machine_by_id(machine_id)

@app.get("/machines")
def get_all_machines_endpoint(block = None, kind = None):
    if block and block not in ["a", "b", "c", "d"]:
        raise HTTPException(status_code=422, detail="Block must be one of: a, b, c, d")
    if kind and kind not in ["washer", "dryer"]:
        raise HTTPException(status_code=422, detail="Kind must be one of: washer, dryer")
        
    return functions.get_all_machines(block, kind)


@app.patch("/update_machine/")
def update_machine(in_service, machine_id):
    if machine_id is None:
        raise HTTPException(status_code = 422, detail = "Machine ID is required")
    if functions.get_machine_by_id(machine_id) is None:
        raise HTTPException(status_code = 404, detail = "Can't find machine with the given ID") 
    return functions.update_machines(in_service, machine_id)


@app.post("/machine/roll_no")
def start_with_roll_no(roll_no, machine_id):
    if roll_no is None:
            raise HTTPException(status_code=400,detail="Roll number is required")
    if machine_id is None:
                raise HTTPException(status_code = 404, detail = "Can't find machine with the given roll_no")
    return functions.start_with_roll_no(roll_no, machine_id)

@app.post("/machine/collect_roll_no")
def collect_by_roll_no(roll_no, machine_id):
     if roll_no is None:
                raise HTTPException(status_code=400,detail="Roll number is required")
     if machine_id is None:
                raise HTTPException(status_code = 404, detail = "Can't find machine with the given roll_no")
     return functions.collect_by_roll_no(roll_no, machine_id)

@app.patch("/machine/not_collected_roll_no")
def not_collected(roll_no, machine_id):
     if roll_no is None:
                raise HTTPException(status_code=400,detail="Roll number is required")
     if machine_id is None:
                    raise HTTPException(status_code = 404, detail = "Can't find machine with the given roll_no")
     return functions.clothes_not_collected(roll_no, machine_id)

@app.get("/get_active_runs_by_rollnumber/{roll_number}")
def get_active_runs_endpoint(roll_number):

    result = functions.get_active_runs_by_rollnumber(roll_number)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="No active runs found for this roll number"
        )

    return result   

@app.get("/machines/attention")
def get_attention_machines():
    return functions.get_machines_needing_attention() 

@app.get("/machines/todays_usage_stats/{block}")
def get_todays_usage_stats(block: str):
    if block not in ["a", "b", "c", "d"]:
        raise HTTPException(
            status_code=422, 
            detail="Block must be one of the following: a, b, c, d"
        )
    return functions.get_todays_usage(block)
