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

def get_client():
    c = Garmin(os.environ["GARMIN_EMAIL"], os.environ["GARMIN_PASSWORD"])
    c.login()
    return c

def pace_target(pace_ms: float) -> dict:
    """Convierte pace en m/s a target de ritmo para Garmin."""
    return {
        "workoutTargetTypeId": 6,
        "workoutTargetTypeKey": "pace.zone",
        "displayOrder": 1,
        "targetValueOne": pace_ms * 0.95,
        "targetValueTwo": pace_ms * 1.05,
    }

@mcp.tool()
def get_today_stats() -> dict:
    """Estadísticas de salud y actividad de hoy"""
    return get_client().get_stats(date.today().isoformat())

@mcp.tool()
def get_heart_rate(days_ago: int = 0) -> dict:
    """Frecuencia cardíaca"""
    d = (date.today() - timedelta(days=days_ago)).isoformat()
    return get_client().get_heart_rates(d)

@mcp.tool()
def get_sleep(days_ago: int = 0) -> dict:
    """Datos de sueño"""
    d = (date.today() - timedelta(days=days_ago)).isoformat()
    return get_client().get_sleep_data(d)

@mcp.tool()
def get_activities(limit: int = 10) -> list:
    """Últimas actividades"""
    return get_client().get_activities(0, limit)

@mcp.tool()
def get_body_composition(days_ago: int = 0) -> dict:
    """Peso y composición corporal"""
    d = (date.today() - timedelta(days=days_ago)).isoformat()
    return get_client().get_body_composition(d)

@mcp.tool()
def get_hrv() -> dict:
    """HRV de hoy"""
    return get_client().get_hrv_data(date.today().isoformat())

@mcp.tool()
def get_training_status() -> dict:
    """Estado de entrenamiento y carga"""
    return get_client().get_training_status(date.today().isoformat())

@mcp.tool()
def get_workouts(limit: int = 20) -> list:
    """Lista de entrenamientos guardados"""
    return get_client().get_workouts(0, limit)

@mcp.tool()
def schedule_workout(workout_id: str, date_str: str) -> dict:
    """Programa un entrenamiento existente. date_str formato YYYY-MM-DD"""
    return get_client().schedule_workout(workout_id, date_str)

@mcp.tool()
def delete_workout(workout_id: str) -> dict:
    """Elimina un entrenamiento"""
    return get_client().delete_workout(workout_id)

@mcp.tool()
def create_running_workout(
    name: str,
    warmup_seconds: int,
    intervals: int,
    interval_seconds: int,
    interval_pace_ms: float,
    recovery_seconds: int,
    recovery_pace_ms: float,
    cooldown_seconds: int,
    schedule_date: str = None
) -> dict:
    """
    Crea un workout de running estructurado.
    Todos los tiempos en segundos.
    pace en metros/segundo: 4:00/km = 4.167, 4:30/km = 3.704, 5:00/km = 3.333, 5:30/km = 3.030, 6:00/km = 2.778.
    schedule_date opcional YYYY-MM-DD para programarlo directo.
    """
    c = get_client()

    warmup = create_warmup_step(
        duration_seconds=float(warmup_seconds),
        step_order=1,
        target_type=pace_target(recovery_pace_ms)
    )

    interval_step = create_interval_step(
        duration_seconds=float(interval_seconds),
        step_order=1,
        target_type=pace_target(interval_pace_ms)
    )

    recovery_step = create_recovery_step(
        duration_seconds=float(recovery_seconds),
        step_order=2,
        target_type=pace_target(recovery_pace_ms)
    )

    repeat = create_repeat_group(
        iterations=intervals,
        workout_steps=[interval_step, recovery_step],
        step_order=2
    )

    cooldown = create_cooldown_step(
        duration_seconds=float(cooldown_seconds),
        step_order=3,
        target_type=pace_target(recovery_pace_ms)
    )

    total_secs = warmup_seconds + intervals * (interval_seconds + recovery_seconds) + cooldown_seconds

    workout = RunningWorkout(
        workoutName=name,
        estimatedDurationInSecs=float(total_secs),
        workoutSegments=[
            WorkoutSegment(
                segmentOrder=1,
                sportType={"sportTypeId": 1, "sportTypeKey": "running"},
                workoutSteps=[warmup, repeat, cooldown]
            )
        ]
    )

    result = c.upload_running_workout(workout)
    workout_id = result.get("workoutId")

    if schedule_date and workout_id:
        c.schedule_workout(workout_id, schedule_date)
        return {"workoutId": workout_id, "scheduled": schedule_date, "name": name}

    return {"workoutId": workout_id, "name": name}

if __name__ == "__main__":
    mcp.run(transport="sse")
