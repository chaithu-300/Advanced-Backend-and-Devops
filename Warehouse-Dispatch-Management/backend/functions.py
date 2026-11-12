from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, create_engine, Float
from sqlalchemy.orm import Session, declarative_base
from fastapi import FastAPI, HTTPException

DB_PATH = "Warehouse.db"
engine = create_engine(f"sqlite:///{DB_PATH}")
Base = declarative_base()

class Package(Base):
    __tablename__ = "packages"

    package_id = Column(Integer, primary_key=True)
    package_name = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    weight = Column(Float, nullable=False)
    arrival_date = Column(DateTime, nullable=False)
    status = Column(String, nullable=False)

class DispatchBatch(Base):
    __tablename__ = "dispatch_batches"

    batch_id = Column(Integer, primary_key=True)
    destination = Column(String, nullable=False)
    vehicle = Column(String, nullable=False)
    status = Column(String, nullable=False)

class BatchPackage(Base):
    __tablename__ = "batch_packages"

    id = Column(Integer, primary_key=True)
    batch_id = Column(Integer, ForeignKey("dispatch_batches.batch_id"), nullable=False)
    package_id = Column(Integer, ForeignKey("packages.package_id"), nullable=False)


Base.metadata.create_all(engine)

def register_package(package):
    session = Session(engine)

    new_package = Package(
        package_name=package["package_name"],
        destination=package["destination"],
        weight=package["weight"],
        arrival_date=package["arrival_date"]
    )

    session.add(new_package)
    session.commit()

    response = {
        "package_id": new_package.package_id,
        "package_name": new_package.package_name,
        "destination": new_package.destination,
        "weight": new_package.weight,
        "arrival_date": str(new_package.arrival_date),
        "status": new_package.status
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
        "arrival_date": str(package.arrival_date),
        "status": package.status
    }

    session.close()
    return response