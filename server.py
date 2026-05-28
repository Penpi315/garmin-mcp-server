import os
from datetime import date, timedelta
from fastmcp import FastMCP
from garminconnect import Garmin
from garminconnect.workout import (
    RunningWorkout, WorkoutSegment, RepeatGroup, ExecutableStep
)

mcp = FastMCP("Garmin Connect")

def get_client():
    c = Garmin(os.environ["GARMIN_EMAIL"], os.environ["GARMIN_PASSWORD"])
    c.login()
    return c

def pace_target(pace_min_km: float) -> dict:
    speed_ms = 1000 / (pace_min_km * 60)
    return {
        "workoutTargetTypeId": 6,
        "workoutTargetTypeKey": "pace.zone",
        "displayOrder": 1,
        "targetValueOne": round(speed_ms * 0.95, 4),
        "targetValueTwo": round(speed_ms * 1.05, 4),
    }

def make_step(step_type_id, step_type_key, display_order, step_order, duration_seconds, target):
    return ExecutableStep(
        stepOrder=step_order,
        stepType={"stepTypeId": step_type_id, "stepTypeKey": step_type_key, "displayOrder": display_order},
        endCondition={"conditionTypeId": 2, "conditionTypeKey": "time", "displayOrder": 2, "displayable": True},
        endConditionValue=float(duration_seconds),
        targetType={"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target", "displayOrder": 1},
        target=target,
    )

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
    interval_pace_min_km: float,
    recovery_seconds: int,
    recovery_pace_min_km: float,
    cooldown_seconds: int,
    schedule_date: str = None
) -> dict:
    """
    Crea un workout de running estructurado con calentamiento, intervalos y enfriamiento.
    interval_pace_min_km y recovery_pace_min_km en min/km decimal (5:30/km = 5.5, 4:00/km = 4.0).
    schedule_date opcional YYYY-MM-DD.
    """
    c = get_client()

    warmup = make_step(1, "warmup", 1, 1, warmup_seconds, pace_target(recovery_pace_min_km))

    interval_step = make_step(3, "interval", 3, 1, interval_seconds, pace_target(interval_pace_min_km))
    recovery_step = make_step(4, "recovery", 4, 2, recovery_seconds, pace_target(recovery_pace_min_km))

    repeat = RepeatGroup(
        stepOrder=2,
        stepType={"stepTypeId": 6, "stepTypeKey": "repeat", "displayOrder": 6},
        numberOfIterations=intervals,
        workoutSteps=[interval_step, recovery_step],
        endCondition={"conditionTypeId": 7, "conditionTypeKey": "iterations", "displayOrder": 7, "displayable": False},
        endConditionValue=float(intervals),
    )

    cooldown = make_step(2, "cooldown", 2, 3, cooldown_seconds, pace_target(recovery_pace_min_km))

    total_secs = float(warmup_seconds + intervals * (interval_seconds + recovery_seconds) + cooldown_seconds)

    workout = RunningWorkout(
        workoutName=name,
        estimatedDurationInSecs=total_secs,
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
