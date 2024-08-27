from flask import jsonify
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from data_management.database import engine
from models import (
    WaterLevel, Hygrometry, SystemState, Precipitation, RainForecast, WateringSession,
    HourlyRain, HourlyTemperature, HourlyWind, HourlySunlight, HourlyHumidity,
    CpuTemperature, TechnicalCabinetConditions
)
from datetime import datetime, timedelta
import calendar

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def convert_to_dict(obj):
    """Convert SQLAlchemy object to dictionary."""
    if obj is None:
        return None
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}

def with_reconnect(func):
    def wrapper(*args, **kwargs):
        session = SessionLocal()
        try:
            return func(session, *args, **kwargs)
        except OperationalError:
            session.rollback()
            # Reconnect logic
            session.close()
            session = SessionLocal()
            return func(session, *args, **kwargs)
        finally:
            session.close()
    return wrapper

@with_reconnect
def get_water_level_data(session):
    try:
        result = session.query(WaterLevel).order_by(WaterLevel.time.desc()).first()
        return f"{result.level:.2f}" if result else "NaN"
    except Exception as error:
        print(f"Erreur lors de la récupération du niveau d'eau depuis la base de données : {error}")
        return "NaN"

@with_reconnect
def get_moisture_data(session, zone):
    try:
        result = session.query(Hygrometry).filter(Hygrometry.zone == zone).order_by(Hygrometry.time.desc()).first()
        return {
            "level": f"{result.level:.2f}",
            "time": result.time.strftime("%Y-%m-%d %H:%M:%S")
        } if result else {"level": "NaN", "time": None}
    except Exception as error:
        print(f"Erreur lors de la récupération de l'humidité pour {zone} depuis la base de données: {error}")
        return {"level": "NaN", "time": None}

@with_reconnect
def get_system_state(session):
    try:
        result = session.query(SystemState).order_by(SystemState.time.desc()).first()
        return {
            "state": result.state,
            "zone": result.zone,
            "source": result.source,
            "mode": result.mode,
            "time": result.time.strftime("%Y-%m-%d %H:%M:%S")
        } if result else {"state": "Unknown", "zone": "N/A", "source": "N/A", "mode": "N/A", "time": None}
    except Exception as error:
        print(f"Erreur lors de la récupération de l'état du système depuis la base de données: {error}")
        return {"state": "Unknown", "zone": "N/A", "source": "N/A", "mode": "N/A", "time": None}

@with_reconnect
def get_last_rain_data(session):
    try:
        result = session.query(Precipitation).order_by(Precipitation.time.desc()).first()
        return f"{result.amount:.2f}" if result else "0.00"
    except Exception as error:
        print(f"Erreur lors de la récupération des données de pluie : {error}")
        return "0.00"

@with_reconnect
def get_water_level_chart_data(session, duration='24h', month=None, year=None):
    try:
        if duration == '24h':
            start_date = datetime.now() - timedelta(days=1)
        elif duration == '7d':
            start_date = datetime.now() - timedelta(days=7)
        elif duration == '30d':
            start_date = datetime.now() - timedelta(days=30)
        elif duration == '365d':
            start_date = datetime.now() - timedelta(days=365)
        elif duration == 'month':
            if month is None:
                month = datetime.now().month
            if year is None:
                year = datetime.now().year
            _, last_day = calendar.monthrange(year, month)
            start_date = datetime(year, month, 1)
            end_date = datetime(year, month, last_day)
        elif duration == 'year':
            if year is None:
                year = datetime.now().year
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31)
        else:
            start_date = datetime.now() - timedelta(days=1)

        end_date = end_date if 'end_date' in locals() else None

        query = session.query(WaterLevel).filter(WaterLevel.time >= start_date)
        if end_date:
            query = query.filter(WaterLevel.time <= end_date)
        results = query.order_by(WaterLevel.time.asc()).all()

        timestamps = [str(result.time) for result in results]
        water_levels = [result.level for result in results]

        return {
            'timestamps': timestamps,
            'water_levels': water_levels
        }
    except Exception as error:
        print(f"Database error: {error}")
        return None

@with_reconnect
def get_watering_sessions(session, limit=20):
    try:
        results = session.query(WateringSession).order_by(WateringSession.time.desc()).limit(limit).all()
        sessions = [convert_to_dict(row) for row in results]
        for session in sessions:
            print(f"Session time: {session['time']}")  # Log the session times
        return sessions
    except Exception as error:
        print(f"Erreur lors de la récupération des sessions d'arrosage: {error}")
        return []

@with_reconnect
def get_yearly_data(session):
    try:
        start_date = datetime(datetime.now().year, 1, 1)
        end_date = datetime(datetime.now().year, 12, 31)

        water_level_data = session.query(WaterLevel).filter(WaterLevel.time.between(start_date, end_date)).all()
        hygrometry_data = session.query(Hygrometry).filter(Hygrometry.time.between(start_date, end_date)).all()
        rain_data = session.query(HourlyRain).filter(HourlyRain.time.between(start_date, end_date)).all()
        watering_sessions_data = session.query(WateringSession).filter(WateringSession.time.between(start_date, end_date)).all()
        temperature_data = session.query(HourlyTemperature).filter(HourlyTemperature.time.between(start_date, end_date)).all()
        sunlight_data = session.query(HourlySunlight).filter(HourlySunlight.time.between(start_date, end_date)).all()
        humidity_data = session.query(HourlyHumidity).filter(HourlyHumidity.time.between(start_date, end_date)).all()
        wind_data = session.query(HourlyWind).filter(HourlyWind.time.between(start_date, end_date)).all()

        return {
            'water_level': [(str(item.time), item.level) for item in water_level_data],
            'hygrometry': [(str(item.time), item.level, item.zone) for item in hygrometry_data],
            'rain': [(str(item.time), item.amount) for item in rain_data],
            'watering_sessions': [(str(item.time), item.zone, item.duration) for item in watering_sessions_data],
            'temperature': [(str(item.time), item.temperature) for item in temperature_data],
            'sunlight': [(str(item.time), item.solar_radiation) for item in sunlight_data],
            'humidity': [(str(item.time), item.humidity) for item in humidity_data],
            'wind': [(str(item.time), item.wind_speed) for item in wind_data]
        }
    except Exception as error:
        print(f"Erreur lors de la récupération des données de l'année en cours : {error}")
        return {}

@with_reconnect
def get_technical_cabinet_data(session):
    try:
        start_date = datetime.now() - timedelta(days=7)

        technical_cabinet_data = session.query(TechnicalCabinetConditions).filter(TechnicalCabinetConditions.time >= start_date).all()
        cpu_temperature_data = session.query(CpuTemperature).filter(CpuTemperature.time >= start_date).all()
        external_temperature_data = session.query(HourlyTemperature).filter(HourlyTemperature.time >= start_date).all()

        return {
            'technical_cabinet': [(str(item.time), item.temperature, item.humidity) for item in technical_cabinet_data],
            'cpu_temperature': [(str(item.time), item.temperature) for item in cpu_temperature_data],
            'external_temperature': [(str(item.time), item.temperature) for item in external_temperature_data]
        }
    except Exception as error:
        print(f"Erreur lors de la récupération des données de la semaine : {error}")
        return {
            'technical_cabinet': [],
            'cpu_temperature': [],
            'external_temperature': []
        }