from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import os


load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
SECRET_KEY = os.getenv('SECRET_KEY')

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Car(Base):
    __tablename__ = 'cars_info'
    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String)
    model = Column(String)
    year = Column(Integer)
    generation = Column(String)
    price = Column(Integer)
    mileage = Column(Integer)
    fuel_type = Column(String)
    transmission = Column(String)
    engine_capacity = Column(Integer)
    vin_code = Column(String)
    add_date = Column(DateTime)
    update_date = Column(DateTime)
    top_lifts = Column(Integer)
    location_id = Column(Integer, ForeignKey('locations.id'))
    location = relationship("Location", back_populates="cars")
    sale_status_id = Column(Integer, ForeignKey('sale_statuses.id'))
    sale_status = relationship("SaleStatus", back_populates="cars")
    accident_id = Column(Integer, ForeignKey('accidents.id'))
    accident = relationship("Accident", back_populates="cars")


class Location(Base):
    __tablename__ = 'locations'
    id = Column(Integer, primary_key=True, index=True)
    location_name = Column(String)
    cars = relationship("Car", back_populates="location")


class SaleStatus(Base):
    __tablename__ = 'sale_statuses'
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String)
    cars = relationship("Car", back_populates="sale_status")


class Accident(Base):
    __tablename__ = 'accidents'
    id = Column(Integer, primary_key=True, index=True)
    was_in_accident = Column(Boolean)
    cars = relationship("Car", back_populates="accident")


Base.metadata.create_all(bind=engine)
