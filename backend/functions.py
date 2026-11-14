from datetime import datetime, timedelta
from platform import machine
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, create_engine, func #pyright: ignore
from sqlalchemy.orm import Session, declarative_base #pyright: ignore
from fastapi import FastAPI, HTTPException #pyright: ignore
import jwt #pyright: ignore
from argon2 import PasswordHasher #pyright: ignore
from argon2.exceptions import VerifyMismatchError #pyright: ignore

ph = PasswordHasher()

DB_PATH = "hostel-laundry.db"
engine = create_engine(f"sqlite:///{DB_PATH}")
Base = declarative_base()

ACCESS_TOKEN_EXPIRY = 15 #mins
REFRESH_TOKEN_EXPIRY = 7 * 24 * 60
SECRET_KEY = "SECRET123"
ALGORITHM = "HS256"

class User(Base):
    __tablename__ = "Users"

    user_id = Column(Integer, primary_key = True)
    user_name = Column(String)
    password = Column(String)

class machines(Base):
    __tablename__ = "machines"
    id = Column(Integer, primary_key = True)
    name = Column(String)
    block = Column(String) #a,b,c,d
    kind = Column(String) #Washer, Dryer
    cycles_minutes = Column(Integer)
    in_service = Column(Integer)

class runs(Base):
    __tablename__ = "runs"
    run_id = Column(Integer, primary_key = True)
    machine_id = Column(Integer, ForeignKey("machines.id"))
    roll_no = Column(String)
    started_at = Column(DateTime, default = datetime.now) #YYYY-MM-DD HH:MM
    ends_at = Column(DateTime)
    collected_at = Column(DateTime) #Empty until collected
    status = Column(String) #Running, Completed, Collected

Base.metadata.create_all(engine)

def register_user(user_name, password):
    session = Session(engine)
    user_exists = session.query(User).filter_by(user_name=user_name).first()
    if user_exists is not None:
        session.close()
        return False
    session.add(User(user_name=user_name, password = ph.hash(password)))
    session.commit()
    session.close()
    return True

def verify_login(username, password):
    session = Session(engine)
    user = session.query(User).filter_by(user_name = username).first()
    if user is None:
        session.close()
        return False
    try:
        ph.verify(user.password, password)
    except VerifyMismatchError:
        session.close()
        return False
    session.close()
    access_token = create_token(username=username, token_type = "access")
    refresh_token = create_token(username=username, token_type = "refresh")
    return {"access_token": access_token, "refresh_token": refresh_token}

def create_token(username, token_type):
    time = ACCESS_TOKEN_EXPIRY
    if token_type == "refresh":
        time = REFRESH_TOKEN_EXPIRY

    payload = {
        "username": username,
        "token_type": token_type,
        "exp": datetime.now() + timedelta(minutes = time)
    }
    token = jwt.encode(payload=payload, key = SECRET_KEY, algorithm = ALGORITHM)
    return token

def verify_token(token):
    try:
        payload = jwt.decode(jwt=token, key=SECRET_KEY, algorithms=[ALGORITHM])

    except:
        return False

    if payload["token_type"] == "access":
        return payload["username"]
    return False

def add_machines(name, block, kind, in_service,cycles_minutes):
    session = Session(engine)
    new_machine = machines(
        name = name,
        block = block,
        kind = kind,
        cycles_minutes = cycles_minutes,
        in_service = in_service
    )
    session.add(new_machine)
    session.commit()

    response = {
        "id": new_machine.id,
        "name": new_machine.name,
        "block": new_machine.block,
        "kind": new_machine.kind,
        "cycles_minutes": new_machine.cycles_minutes,
        "in_service": new_machine.in_service
    }
    session.close()
    return response

def get_machine_by_id(machine_id):
    session = Session(engine)
    machine = session.query(machines).filter(machines.id == machine_id).first()
    if machine is None:
        session.close()
        return None
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    state = "free"
    minutes_left = 0
    
    if machine.in_service == 0:
        state = "out of order"
    else:
        active_run = session.query(runs).filter(
            runs.machine_id == machine.id,
            runs.status == "running",
            runs.collected_at == None
        ).first()
        
        if active_run:
            if now_str < active_run.ends_at:
                state = "running"
                dt_now = datetime.strptime(now_str, "%Y-%m-%d %H:%M")
                dt_ends = datetime.strptime(active_run.ends_at, "%Y-%m-%d %H:%M")
                minutes_left = max(0, int((dt_ends - dt_now).total_seconds() / 60))
            else:
                state = "completed"
    recent_history = session.query(runs).filter(
        runs.machine_id == machine.id
    ).order_by(runs.run_id).all()
    runs_list = []
    for r in recent_history:
        runs_list.append({
            "id": r.run_id,
            "roll_no": r.roll_no,
            "started_at": r.started_at,
            "ends_at": r.ends_at,
            "collected_at": r.collected_at,
            "status": r.status
        })
        
    response = {
        "id": machine.id,
        "name": machine.name,
        "block": machine.block,
        "kind": machine.kind,
        "cycle_minutes": machine.cycles_minutes,
        "in_service": machine.in_service,
        "state": state,
        "minutes_left": minutes_left,
        "recent_runs": runs_list
    }
    
    session.close()
    return response

def get_all_machines(block=None, kind=None):
    session = Session(engine)
    query = session.query(machines)

    if block:
        query = query.filter(machines.block == block)

    if kind:
        query = query.filter(machines.kind == kind)

    all_machines = query.all()
    response = []
    now_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    for machine in all_machines:
        state = "free"
        minutes_left = 0
        
        if machine.in_service == 0:
            state = "out of order"
        else:
            active_run = session.query(runs).filter(
                runs.machine_id == machine.id,
                runs.status == "running",
                runs.collected_at == None
            ).first()
            
            if active_run:
                if now_time < active_run.ends_at:
                    state = "running"
                    dt_now = datetime.strptime(now_time, "%Y-%m-%d %H:%M")
                    dt_ends = datetime.strptime(active_run.ends_at, "%Y-%m-%d %H:%M")
                    minutes_left = max(0, int((dt_ends - dt_now).total_seconds() / 60))
                else:
                    state = "Completed"
                    
        response.append({
            "id": machine.id,
            "name": machine.name,
            "block": machine.block,
            "kind": machine.kind,
            "cycle_minutes": machine.cycles_minutes,
            "in_service": machine.in_service,
            "state": state,
            "minutes_left": minutes_left
        })
        
    session.close()
    return response

def update_machines(in_service, machine_id):
    session = Session(engine)
    machine = session.query(machines).filter(machines.id == machine_id).first()
    machine.in_service = in_service
    session.commit()
    response = {
        "Machine status updated successfully"
    }
    session.close()
    return response

def start_with_roll_no(roll_no, machine_id): #Start a machine with a roll number. It starts now and ends after the machine's cycle minutes.
    session = Session(engine)
    run = runs(roll_no=roll_no,machine_id=machine_id)
    session.add(run)
    machine = session.query(machines).filter(machines.id == machine_id).first()
    if machine.in_service == 0:
        raise HTTPException(status_code=400,detail="Machine is out of service")
    session.commit()
    
    response = {
        "id": run.machine_id,
        "started_at" : run.started_at,
        "ends_at" : run.ends_at
    }
    session.close()
    return response

def collect_by_roll_no(roll_no,machine_id):
    session =Session(engine)
    
    run = runs(roll_no=roll_no,machine_id=machine_id)
    session.add(run)
    session.commit()
    
    response = {
        "started_id":run.started_at,
       "collected_at":run.collected_at,
    }
    session.close()
    return response
    
def clothes_not_collected(roll_no,machine_id=None):
    session=Session(engine)
    
    run = session.query(runs).filter(runs.roll_no == roll_no,runs.machine_id == machine_id).first()

    if not run:
        raise HTTPException(status_code = 404,detail="No matching run found")
    if run.status != "Completed":
        raise HTTPException(status_code=400,detail="Only completed runs can be cleared")

    run.status = "Not collected"
    
    session.commit()
    response ={
        "roll_no": run.roll_no,
        "machine_id":run.machine_id,
        "collected_at" : run.collected_at,
        "status":run.status,     
    }
    session.close()
    return response

def get_active_runs_by_rollnumber(roll_number):

    session = Session(engine)

    active_runs = session.query(runs).filter(
        runs.roll_no == roll_number,
        runs.collected_at == None
    ).all()

    response = []

    for run in active_runs:
        response.append({
            "id": run.run_id,
            "machine_id": run.machine_id,
            "roll_no": run.roll_no,
            "status": run.status,
            "ends_at": run.ends_at
        })

    session.close()

    return response

def get_machines_needing_attention():
    session = Session(engine)
    Machines = session.query(machines).all()
    response = []
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    for Machine in Machines:
        Runs = session.query(runs).filter(
            runs.machine_id == Machine.id,
            runs.status == "running"
        ).all()
        if Machine.in_service == 0:
            detail = "Out of order"
        for Run in Runs:
            if current_time > (Run.ends_at + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M"):
                detail = "Waiting for pickup"
        if Machine.in_service == 0:
            temp_Machine = {
                "id": Machine.id,
                "name": Machine.name,
                "block": Machine.block,
                "kind": Machine.kind,
                "detail": detail
            }
            response.append(temp_Machine)
    session.close()
    return response

def get_todays_usage(block):
    session = Session(engine)
    today_time = datetime.now().strftime("%Y-%m-%d") 
    results = session.query(
        machines.kind,
        func.count(runs.run_id)).join(runs, machines.id == runs.machine_id).filter(machines.block == block,runs.started_at.like(f"{today_time}%")
    ).group_by(
        machines.kind
    ).all()
    washer_count = 0
    dryer_count = 0
    for row in results:
        kind, count = row
        if kind.lower() == "washer":
            washer_count = count
        elif kind.lower() == "dryer":
            dryer_count = count
            
    response = {
        "block": block,
        "washer_runs": washer_count,
        "dryer_runs": dryer_count
    }
    
    session.close()
    return response