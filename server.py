import os
from datetime import date, timedelta
from fastmcp import FastMCP
from garminconnect import Garmin

mcp = FastMCP("Garmin Connect")

def client():
    c = Garmin(os.environ["GARMIN_EMAIL"], os.environ["GARMIN_PASSWORD"])
    c.login()
    return c

@mcp.tool()
def get_today_stats() -> dict:
    """Estadísticas de salud y actividad de hoy"""
    return client().get_stats(date.today().isoformat())

@mcp.tool()
def get_heart_rate(days_ago: int = 0) -> dict:
    """Frecuencia cardíaca. days_ago=0 es hoy"""
    d = (date.today() - timedelta(days=days_ago)).isoformat()
    return client().get_heart_rates(d)

@mcp.tool()
def get_sleep(days_ago: int = 0) -> dict:
    """Datos de sueño"""
    d = (date.today() - timedelta(days=days_ago)).isoformat()
    return client().get_sleep_data(d)

@mcp.tool()
def get_activities(limit: int = 10) -> list:
    """Últimas actividades"""
    return client().get_activities(0, limit)

@mcp.tool()
def get_body_composition(days_ago: int = 0) -> dict:
    """Peso y composición corporal"""
    d = (date.today() - timedelta(days=days_ago)).isoformat()
    return client().get_body_composition(d)

@mcp.tool()
def get_hrv() -> dict:
    """HRV (Heart Rate Variability) de hoy"""
    return client().get_hrv_data(date.today().isoformat())

@mcp.tool()
def get_training_status() -> dict:
    """Estado de entrenamiento y carga"""
    return client().get_training_status(date.today().isoformat())

@mcp.tool()
def get_workouts(limit: int = 20) -> list:
    """Lista de entrenamientos guardados en Garmin"""
    return client().get_workouts(0, limit)

@mcp.tool()
def schedule_workout(workout_id: str, date_str: str) -> dict:
    """Programa un entrenamiento. date_str formato YYYY-MM-DD"""
    return client().schedule_workout(workout_id, date_str)

@mcp.tool()
def delete_workout(workout_id: str) -> dict:
    """Elimina un entrenamiento guardado"""
    return client().delete_workout(workout_id)

@mcp.tool()
def get_weekly_summary() -> dict:
    """Resumen semanal de actividad"""
    c = client()
    today = date.today().isoformat()
    week_ago = (date.today() - timedelta(days=7)).isoformat()
    return c.get_weekly_stress(today)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    mcp.run(transport="sse", host="0.0.0.0", port=port)
