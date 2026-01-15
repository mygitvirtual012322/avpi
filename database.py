import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Database URL from environment (Railway injects this automatically)
DATABASE_URL = os.environ.get('DATABASE_URL')

# SQLite fallback for local development
if not DATABASE_URL:
    DATABASE_URL = 'sqlite:///./ipva_local.db'
else:
    # Fix for Railway's postgres:// vs postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class Config(Base):
    __tablename__ = 'config'
    
    id = Column(Integer, primary_key=True)
    pix_key = Column(String(100))
    pix_name = Column(String(100))
    pix_city = Column(String(100))
    pix_description = Column(String(200))
    updated_at = Column(DateTime, default=datetime.utcnow)

class Consultation(Base):
    __tablename__ = 'consultations'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    plate = Column(String(20))
    vehicle = Column(String(200))
    ipva_value = Column(String(50))

class PixGenerated(Base):
    __tablename__ = 'pix_generated'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    plate = Column(String(20))
    amount = Column(String(50))
    code = Column(Text)

class UserSession(Base):
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    utm_source = Column(String(50))
    ip_address = Column(String(50))
    current_stage = Column(String(50))
    plate = Column(String(20))
    pix_copied = Column(Boolean, default=False)
    pix_copied_at = Column(DateTime, nullable=True)
    stages = Column(JSON)  # Store stage history as JSON

class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(String(50), unique=True, index=True)
    session_id = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Vehicle data
    plate = Column(String(20))
    brand = Column(String(200))
    model = Column(String(200))
    year = Column(String(10))
    color = Column(String(50))
    fuel = Column(String(50))
    state = Column(String(50))
    city = Column(String(100))
    chassis = Column(String(100))
    engine = Column(String(100))
    
    # Payment data
    ipva_original = Column(String(50))
    ipva_discounted = Column(String(50))
    licensing_fee = Column(String(50))
    installment_count = Column(Integer)
    installment_value = Column(String(50))
    first_payment_total = Column(String(50))
    discount_percentage = Column(Integer)
    
    # Installments (stored as JSON)
    installments = Column(JSON)
    
    # Tracking
    pix_generated = Column(Boolean, default=False)
    pix_generated_at = Column(DateTime, nullable=True)
    pix_copied = Column(Boolean, default=False)
    pix_copied_at = Column(DateTime, nullable=True)
    pix_code = Column(Text, nullable=True)

class MetaPixelConfig(Base):
    __tablename__ = 'meta_pixel_config'
    
    id = Column(Integer, primary_key=True)
    pixel_id = Column(String(50))
    enabled = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow)

# Create all tables
def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == '__main__':
    init_db()
