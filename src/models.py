"""
models.py
"""
import re
from pydantic import BaseModel, field_validator
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class PhoneNumberDB(Base):
    __tablename__ = 'phone_numbers'

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String, nullable=False)
    organization_id = Column(Integer, ForeignKey('organizations.id'))

    organization = relationship("Organization", back_populates="phone_numbers", lazy="selectin")


class Building(Base):
    __tablename__ = 'buildings'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    address = Column(String, unique=True)
    latitude = Column(Float)
    longitude = Column(Float)

    organizations = relationship("Organization", back_populates="building", lazy="selectin")


class Activity(Base):
    __tablename__ = 'activities'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True)
    parent_id = Column(Integer, ForeignKey('activities.id'))
    level = Column(Integer)

    sub_activities = relationship("Activity")
    organizations = relationship("OrganizationActivity", back_populates="activity", lazy="selectin")


class Organization(Base):
    __tablename__ = 'organizations'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True)
    building_id = Column(Integer, ForeignKey('buildings.id'))

    building = relationship("Building", back_populates="organizations", lazy="selectin")
    activities = relationship("OrganizationActivity", back_populates="organization", lazy="selectin")
    phone_numbers = relationship("PhoneNumberDB", back_populates="organization", lazy="selectin")


class OrganizationActivity(Base):
    __tablename__ = 'organization_activities'

    organization_id = Column(Integer, ForeignKey('organizations.id'), primary_key=True)
    activity_id = Column(Integer, ForeignKey('activities.id'), primary_key=True)

    organization = relationship("Organization", back_populates="activities", lazy="selectin")
    activity = relationship("Activity", back_populates="organizations", lazy="selectin")


class PhoneNumber(BaseModel):
    number: str
    organization_id: int

    @field_validator('number')
    def validate_number(cls, value):
        if not re.match(r'^\+7\d{10}$', value):
            raise ValueError('Номер телефона должен соответствовать формату +7XXXXXXXXXX')
        return value

    class Config:
        from_attributes = True
