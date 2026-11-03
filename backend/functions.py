from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base
from fastapi import FastAPI, HTTPException

DB_PATH = "hostel-laundry.db"
engine = create_engine(f"sqlite:///{DB_PATH}")
Base = declarative_base()

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

def add_machines(name, block, kind, cycles_minutes, in_service):
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

def get_machines_by_id(machine_id):
    session = Session(engine)
    machine = session.get(machines, machine_id)
    if machine is None:
        raise HTTPException(status_code = 404, detail = "Can't find machine with the given ID")
    response = {
        "id": machine.id,
        "name": machine.name,
        "block": machine.block,
        "kind": machine.kind,
        "cycles_minutes": machine.cycles_minutes,
        "in_service": machine.in_service
    }
    session.close()
    return response

def get_machines(block = False, kind = False):
    session = Session(engine)
    Machines = session.query(machines).all()
    response = []
    for Machine in Machines:
        temp_Machine = {
            "id": Machine.id,
            "name": Machine.name,
            "block": Machine.block,
            "kind": Machine.kind,
            "cycles_minutes": Machine.cycles_minutes,
            "in_service": Machine.in_service
        }
        response.append(temp_Machine)
    session.close()
    return response

def update_machines(in_service, machine_id):
    session = Session(engine)
    machine = session.query(machines).filter(machines.id == machine_id).first()
    if machine is None:
        raise HTTPException(status_code = 404, detail = "Can't find machine with the given ID")
    machine.in_service = in_service
    session.commit()
    response = {
        "Machine status updated successfully"
    }
    session.close()
    return response
    