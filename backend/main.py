from typing import Literal

from fastapi import FastAPI, HTTPException, Header #pyright: ignore
import functions
from fastapi.middleware.cors import CORSMiddleware #pyright: ignore
from pydantic import BaseModel, Field #pyright: ignore

app = FastAPI()

class AddMachineRequest(BaseModel):
    name: str = Field(min_length=1)
    block: Literal["a", "b", "c", "d"]
    kind: Literal["washer", "dryer"]
    cycles_minutes: int = Field(ge=20, le=90)
    in_service: int = Field(default=1, ge=0, le=1)


class UpdateMachineRequest(BaseModel):
    machine_id: int
    in_service: int = Field(ge=0, le=1)

class RunRequest(BaseModel):
    roll_no: str = Field(min_length=1)
    machine_id: int

class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)

class RegisterRequest(BaseModel):
    user_name: str = Field(min_length=1)
    password: str = Field(min_length=1)


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
def add_machine(data: AddMachineRequest, token = Header(None)):
    username = functions.verify_token(token=token)
    if not username:
          raise HTTPException(status_code = 401, detail = "Invalid or Expired token")
    return functions.add_machines(data.name, data.block, data.kind, data.in_service, data.cycles_minutes)

@app.get("/machines_by_id/{machine_id}")
def get_single_machine_endpoint(machine_id: int, token = Header(None)):
    username = functions.verify_token(token=token)
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or Expired token")
    machine = functions.get_machine_by_id(machine_id)
    if machine is None:
        raise HTTPException(status_code = 404, detail = "Machine not found")
    return machine

@app.get("/machines")
def get_all_machines_endpoint(block = None, kind = None, token = Header(None)):
    username = functions.verify_token(token=token)
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or Expired token")
    if block and block not in ["a", "b", "c", "d"]:
        raise HTTPException(status_code=422, detail="Block must be one of: a, b, c, d")
    if kind and kind not in ["washer", "dryer"]:
        raise HTTPException(status_code=422, detail="Kind must be one of: washer, dryer")

    return functions.get_all_machines(block, kind)


@app.patch("/update_machine/")
def update_machine(data: UpdateMachineRequest, token = Header(None)):
    username = functions.verify_token(token=token)
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or Expired token")
    if functions.get_machine_by_id(data.machine_id) is None:
        raise HTTPException(status_code = 404, detail = "Can't find machine with the given ID")
    return functions.update_machines(data.in_service, data.machine_id)


@app.post("/machine/roll_no")
def start_with_roll_no(data: RunRequest, token = Header(None)):
    username = functions.verify_token(token=token)
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or Expired token")
    if functions.get_machine_by_id(data.machine_id) is None:
        raise HTTPException(status_code = 404, detail = "Can't find machine with the given ID")
    return functions.start_with_roll_no(data.roll_no, data.machine_id)

@app.post("/machine/collect_roll_no")
def collect_by_roll_no(data: RunRequest, token = Header(None)):
    username = functions.verify_token(token=token)
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or Expired token")
    if functions.get_machine_by_id(data.machine_id) is None:
        raise HTTPException(status_code = 404, detail = "Can't find machine with the given ID")
    return functions.collect_by_roll_no(data.roll_no, data.machine_id)

@app.patch("/machine/not_collected_roll_no")
def not_collected(data: RunRequest, token = Header(None)):
    username = functions.verify_token(token=token)
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or Expired token")
    if functions.get_machine_by_id(data.machine_id) is None:
        raise HTTPException(status_code = 404, detail = "Can't find machine with the given ID")
    return functions.clothes_not_collected(data.roll_no, data.machine_id)

@app.get("/get_active_runs_by_rollnumber/{roll_number}")
def get_active_runs_endpoint(roll_number, token = Header(None)):
    username = functions.verify_token(token=token)
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or Expired token")

    result = functions.get_active_runs_by_rollnumber(roll_number)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="No active runs found for this roll number"
        )

    return result

@app.get("/machines/attention")
def get_attention_machines(token = Header(None)):
    username = functions.verify_token(token=token)
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or Expired token")
    return functions.get_machines_needing_attention()

@app.get("/machines/todays_usage_stats/{block}")
def get_todays_usage_stats(block: str, token = Header(None)):
    username = functions.verify_token(token=token)
    if not username:
        raise HTTPException(status_code = 401, detail = "Invalid or Expired token")
    if block not in ["a", "b", "c", "d"]:
        raise HTTPException(
            status_code=422,
            detail="Block must be one of the following: a, b, c, d"
        )
    return functions.get_todays_usage(block)

@app.post("/login")
def login(data: LoginRequest):
     token = functions.verify_login(username=data.username, password=data.password)
     if not token:
          raise HTTPException(status_code = 401, detail = "Invalid Credentials")
     return {"token": token}

@app.post("/register")
def register_user(data: RegisterRequest):
     if functions.register_user(user_name=data.user_name, password=data.password):
          return {"message": "user registered successfully"}
     raise HTTPException(status_code = 400, detail = "user already exists")

@app.post("/refresh")
def refresh(refresh_token = Header(None)):
     username = functions.verify_token(token = refresh_token)
     if not username:
          raise HTTPException(status_code=401, detail = "Invalid or Expired refresh token")
     access_token = functions.create_token(username=username, token_type="access")
     return {"access_token": access_token}