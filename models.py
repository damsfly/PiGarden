from sqlalchemy import Column, Integer, String, DateTime, Float, TIMESTAMP, text
from data_management.database import Base  # Importer Base depuis database.py

class Log(Base):
    __tablename__ = 'logs'
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    data = Column(String(255), nullable=False)  # Définir une longueur pour VARCHAR

class CpuTemperature(Base):
    __tablename__ = 'cpu_temperature'
    id = Column(Integer, primary_key=True, index=True)
    time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    temperature = Column(Float, nullable=False)

class TechnicalCabinetConditions(Base):
    __tablename__ = 'technical_cabinet_conditions'
    id = Column(Integer, primary_key=True, index=True)
    time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)

class WaterLevel(Base):
    __tablename__ = 'water_level'
    id = Column(Integer, primary_key=True, index=True)
    time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    level = Column(Float, nullable=False)

class RainForecast(Base):
    __tablename__ = 'rain_forecast'
    id = Column(Integer, primary_key=True, index=True)
    time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    amount = Column(Float, nullable=False)

class Precipitation(Base):
    __tablename__ = 'precipitation'
    id = Column(Integer, primary_key=True, index=True)
    time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    amount = Column(Float, nullable=False)

class Hygrometry(Base):
    __tablename__ = 'hygrometry'
    id = Column(Integer, primary_key=True, index=True)
    time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    level = Column(Float, nullable=False)
    zone = Column(String(100), nullable=False)  # Définir une longueur pour VARCHAR

class SystemState(Base):
    __tablename__ = 'system_state'
    id = Column(Integer, primary_key=True, index=True)
    time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    state = Column(String(50), nullable=False)  # Définir une longueur pour VARCHAR
    zone = Column(String(100), nullable=False)  # Définir une longueur pour VARCHAR
    source = Column(String(50), nullable=False)  # Définir une longueur pour VARCHAR
    mode = Column(String(50), nullable=False)  # Définir une longueur pour VARCHAR

class WateringSession(Base):
    __tablename__ = 'watering_sessions'
    id = Column(Integer, primary_key=True, index=True)
    time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    zone = Column(String(100), nullable=False)  # Définir une longueur pour VARCHAR
    duration = Column(Integer, nullable=False)
    source = Column(String(50), nullable=False)  # Définir une longueur pour VARCHAR
    soil_moisture_before = Column(Float)
    mode = Column(String(50), nullable=False, default='Automatic')  # Définir une longueur pour VARCHAR

class HourlyRain(Base):
    __tablename__ = 'hourly_rain'
    id = Column(Integer, primary_key=True, index=True)
    time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    amount = Column(Float, nullable=False)

class HourlyTemperature(Base):
    __tablename__ = 'hourly_temperature'
    id = Column(Integer, primary_key=True, index=True)
    time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    temperature = Column(Float, nullable=False)

class HourlyWind(Base):
    __tablename__ = 'hourly_wind'
    id = Column(Integer, primary_key=True, index=True)
    time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    wind_speed = Column(Float, nullable=False)

class HourlySunlight(Base):
    __tablename__ = 'hourly_sunlight'
    id = Column(Integer, primary_key=True, index=True)
    time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    solar_radiation = Column(Float, nullable=False)

class HourlyHumidity(Base):
    __tablename__ = 'hourly_humidity'
    id = Column(Integer, primary_key=True, index=True)
    time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    humidity = Column(Float, nullable=False)