import os
from datetime import date, timedelta
from fastmcp import FastMCP
from garminconnect import Garmin
from garminconnect.workout import (
    RunningWorkout, WorkoutSegment,
    create_warmup_step, create_interval_step,
    create_recovery_step, create_cooldown_step,
    create_repeat_group,
)

mcp = FastMCP("Garmin Connect")

garmin = Garmin(os.environ["GARMIN_EMAIL"], os.environ["GARMIN_PASSWORD"])
garmin.login()

@mcp.tool()
def get_today_stats() -> dict:
    """Estadísticas de salud y actividad de hoy"""
    return garmin.get_stats(date.today().isoformat())

@mcp.tool()
def get_heart_rate(days_ago: int = 0) -> dict:
    """Frecuencia cardíaca"""
    d = (date.today() - timedelta(days=days_ago)).isoformat()
    return garmin.get_heart_rates(d)

@mcp.tool()
def get_sleep(days_ago: int = 0) -> dict:
    """Datos de sueño"""
    d = (date.today() - timedelta(days=days_ago)).isoformat()
    return garmin.get_sleep_data(d)

@mcp.tool()
def get_activities(limit: int = 10) -> list:
    """Últimas actividades"""
    return garmin.get_activities(0, limit)

@mcp.tool()
def get_body_composition(days_ago: int = 0) -> dict:
    """Peso y composición corporal"""
    d = (date.today() - timedelta(days=days_ago)).isoformat()
    return garmin.get_body_composition(d)

@mcp.tool()
def get_hrv() -> dict:
    """HRV de hoy"""
    return garmin.get_hrv_data(date.today().isoformat())

@mcp.tool()
def get_training_status() -> dict:
    """Estado de entrenamiento y carga"""
    return garmin.get_training_status(date.today().isoformat())

@mcp.tool()
def get_workouts(limit: int = 20) -> list:
    """Lista de entrenamientos guardados"""
    return garmin.get_workouts(0, limit)

@mcp.tool()
def schedule_workout(workout_id: str, date_str: str) -> dict:
    """Programa un entrenamiento existente. date_str formato YYYY-MM-DD"""
    return garmin.schedule_workout(workout_id, date_str)

@mcp.tool()
def delete_workout(workout_id: str) -> dict:
    """Elimina un entrenamiento"""
    return garmin.delete_workout(workout_id)

@mcp.tool()
def create_running_workout(
    name: str,
    warmup_seconds: int,
    intervals: int,
    interval_distance_meters: float,
    interval_pace_ms: float,
    recovery_distance_meters: float,
    recovery_pace_ms: float,
    cooldown_seconds: int,
    schedule_date: str = None
) -> dict:
    """
    Crea un workout de running estructurado con calentamiento, intervalos y enfriamiento.
    pace en metros/segundo (ej: 4:00/km = 4.167 m/s).
    schedule_date opcional en formato YYYY-MM-DD para programarlo directo.
    """
    workout = RunningWorkout(
        workoutName=name,
        estimatedDurationInSecs=(
            warmup_seconds +
            intervals * (interval_distance_meters / interval_pace_ms +
                         recovery_distance_meters / recovery_pace_ms) +
            cooldown_seconds
        ),
        workoutSegments=[
            WorkoutSegment(
                segmentOrder=1,
                sportType={"sportTypeId": 1, "sportTypeKey": "running"},
                workoutSteps=[
                    create_warmup_step(float(warmup_seconds)),
                    create_repeat_group(
                        iterations=intervals,
                        steps=[
                            create_interval_step(distance=interval_distance_meters, pace=interval_pace_ms),
                            create_recovery_step(distance=recovery_distance_meters, pace=recovery_pace_ms),
                        ]
                    ),
                    create_cooldown_step(float(cooldown_seconds)),
                ]
            )
        ]
    )

    result = garmin.upload_running_workout(workout)
    workout_id = result.get("workoutId")

    if schedule_date and workout_id:
        garmin.schedule_workout(workout_id, schedule_date)
        return {"workoutId": workout_id, "scheduled": schedule_date, "name": name}

    return {"workoutId": workout_id, "name": name}

if __name__ == "__main__":
    mcp.run(transport="sse")
