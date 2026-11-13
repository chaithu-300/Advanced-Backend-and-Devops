from datetime import datetime, timedelta
from sqlalchemy import Column, ForeignKey, Integer, String, create_engine, Float, Date #pyright: ignore
from sqlalchemy.orm import Session, declarative_base #pyright: ignore
from fastapi import FastAPI, HTTPException #pyright: ignore
import jwt #pyright: ignore
from argon2 import PasswordHasher #pyright: ignore
from argon2.exceptions import VerifyMismatchError #pyright: ignore

ph = PasswordHasher()

DB_PATH = "Warehouse.db"
engine = create_engine(f"sqlite:///{DB_PATH}")
Base = declarative_base()

USERNAME = "chaithu"
PASSWORD = "123456"
ACCESS_TOKEN_EXPIRY = 15 #mins
REFRESH_TOKEN_EXPIRY = 7 * 24 * 60
SECRET_KEY = "SECRET123"
ALGORITHM = "HS256"

class User(Base):
    __tablename__ = "Users"

    user_id = Column(Integer, primary_key = True)
    user_name = Column(String)
    password = Column(String)
    

class Package(Base):
    __tablename__ = "packages"

    package_id = Column(Integer, primary_key=True)
    package_name = Column(String)
    destination = Column(String)
    weight = Column(Float)
    arrival_date = Column(Date)
    status = Column(String, default = "pending")

class DispatchBatch(Base):
    __tablename__ = "dispatch_batches"

    batch_id = Column(Integer, primary_key=True)
    destination = Column(String)
    vehicle = Column(String)
    status = Column(String, default = "planned")

class BatchPackage(Base):
    __tablename__ = "batch_packages"

    id = Column(Integer, primary_key=True)
    batch_id = Column(Integer, ForeignKey("dispatch_batches.batch_id"))
    package_id = Column(Integer, ForeignKey("packages.package_id"))


Base.metadata.create_all(engine)

def register_user(user_name,password):
    session = Session(engine)
    user_exists=session.query(User).filter_by(user_name=user_name).first()
    if user_exists is not None:
        session.close()
        return False
    session.add(User(user_name=user_name,password =ph.hash(password)))
    session.commit()
    session.close()
    return True


def register_package(package_name, destination, weight, arrival_date):
    session = Session(engine)
    new_package = Package(
        package_name = package_name,
        destination = destination,
        weight = weight,
        arrival_date = arrival_date
    )
    session.add(new_package)
    session.commit()

    response = {
        "id": new_package.package_id,
        "name": new_package.package_name,
        "destination": new_package.destination,
        "weight": new_package.weight,
        "arrival_date": new_package.arrival_date
    }
    session.close()
    return response


def get_package(package_id):
    session = Session(engine)

    package = session.query(Package).filter(
        Package.package_id == package_id
    ).first()

    if package is None:
        session.close()
        return None

    response = {
        "package_id": package.package_id,
        "package_name": package.package_name,
        "destination": package.destination,
        "weight": package.weight,
        "arrival_date": package.arrival_date,
        "status": package.status
    }

    session.close()
    return response

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
    access_token = create_token(username=username, token_type="access")
    refresh_token = create_token(username=username, token_type="refresh")
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
    token = jwt.encode(payload=payload, key=SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_token(token):
    try:
        payload = jwt.decode(jwt=token,key=SECRET_KEY,algorithms=[ALGORITHM])

    except:
        return False

    if payload["token_type"] == "access":
        return payload["username"]

    return False


def update_package(package_id, package_name=None, destination=None, weight=None, arrival_date=None, status=None):
    session = Session(engine)

    package = session.query(Package).filter(Package.package_id == package_id).first()
    if package is None:
        session.close()
        return None

    if package_name is not None:
        package.package_name = package_name

    if destination is not None:
        package.destination = destination

    if weight is not None:
        package.weight = weight

    if arrival_date is not None:
        package.arrival_date = arrival_date

    if status is not None:
        package.status = status

    session.commit()

    response = {
        "package_id": package.package_id,
        "package_name": package.package_name,
        "destination": package.destination,
        "weight": package.weight,
        "arrival_date": package.arrival_date,
        "status": package.status
    }

    session.close()
    return response

def delete_package(package_id):
    session = Session(engine)

    package = session.query(Package).filter(Package.package_id == package_id).first()
    if package is None:
        session.close()
        return None

    if package.status == "assigned" or package.status == "dispatched":
        session.close()
        return "cannot delete"

    session.delete(package)
    session.commit()

    session.close()
    return "deleted"


def search_by_filter(destination = None, arrival_date = None, status = None):
    session = Session(engine)
    query = session.query(Package)

    if destination:
        query = query.filter(Package.destination == destination)

    if arrival_date:
        query = query.filter(Package.arrival_date == arrival_date)

    if status:
        query = query.filter(Package.status == status)

    results = []
    for package in query.all():
        results.append({
            "package_id": package.package_id,
            "package_name": package.package_name,
            "destination": package.destination,
            "weight": package.weight,
            "arrival_date": package.arrival_date,
            "status": package.status
        })

    session.close()
    return results


def search_dispatch_batches(destination=None, vehicle=None, status=None):
    session = Session(engine)

    query = session.query(DispatchBatch)

    if destination:
        query = query.filter(DispatchBatch.destination == destination)

    if vehicle:
        query = query.filter(DispatchBatch.vehicle == vehicle)

    if status:
        query = query.filter(DispatchBatch.status == status)

    results = []

    for batch in query.all():
        results.append({
            "batch_id": batch.batch_id,
            "destination": batch.destination,
            "vehicle": batch.vehicle,
            "status": batch.status
        })

    session.close()
    return results

def get_warehouse_statistics():
    session = Session(engine)

    packages = session.query(Package).all()

    total_received = len(packages)
    pending = 0
    dispatched = 0
    destination_count = {}

    for package in packages:

        if package.status == "pending":
            pending += 1

        if package.status == "dispatched":
            dispatched += 1

        if package.destination in destination_count:
            destination_count[package.destination] += 1
        else:
            destination_count[package.destination] = 1

    session.close()

    return {
        "total_received": total_received,
        "pending": pending,
        "dispatched": dispatched,
        "destination_wise_count": destination_count
    }


def create_dispatch_batch(destination, vehicle, package_ids):
    session = Session(engine)

    if len(package_ids) == 0:
        session.close()
        return "no packages provided"

    for package_id in package_ids:

        package = session.query(Package).filter(
            Package.package_id == package_id
        ).first()

        if package is None:
            session.close()
            return "package not found"

        if package.destination != destination:
            session.close()
            return "destination mismatch"

        if package.status == "assigned" or package.status == "dispatched":
            session.close()
            return "package already assigned or dispatched"

    batch = DispatchBatch(
        destination=destination,
        vehicle=vehicle,
        status="planned"
    )

    session.add(batch)
    session.commit()

    for package_id in package_ids:

        batch_package = BatchPackage(batch_id=batch.batch_id,package_id=package_id)

        session.add(batch_package)

        package = session.query(Package).filter(Package.package_id == package_id).first()

        package.status = "assigned"

    session.commit()

    response = {
        "batch_id": batch.batch_id,
        "destination": batch.destination,
        "vehicle": batch.vehicle,
        "status": batch.status,
        "package_ids": package_ids
    }

    session.close()

    return response



    



        