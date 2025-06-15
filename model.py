# model.py
from datetime import date
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String
from flask_login import UserMixin


db = SQLAlchemy()

from flask_login import UserMixin

class UserDetails(db.Model, UserMixin):  # Add UserMixin here
    __tablename__ = 'user_details'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    profile_completed = db.Column(db.Boolean, default=False)

    # Additional fields
    name = db.Column(db.String(100))
    aadhar_number = db.Column(db.String(20))
    income = db.Column(db.String(20))
    religion = db.Column(db.String(50))
    community = db.Column(db.String(50))
    occupation = db.Column(db.String(50))
    education_qualification = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
from datetime import date

class Scheme(db.Model):
    __tablename__ = 'scheme'
    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String)
    description = db.Column(db.String)
    min_age = db.Column(db.Integer)
    max_age = db.Column(db.Integer)
    posted_date = db.Column(db.Date, default=date.today)
    last_date = db.Column(db.Date, default=date.today)  # Set default to current date
    min_income = db.Column(db.Float)
    max_income = db.Column(db.Float)
    community = db.Column(db.String)
    link = db.Column(db.String(300))
