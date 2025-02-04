from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select, and_
from extensions import db
from app.models import CompetitionQuiz
from flask import Flask

from app.services import CompetitionQuizService

def check_pending_quizzes(app: Flask):
    """Ejecuta la verificación de quizzes pendientes con el contexto de Flask."""
    # Crea y activa manualmente el contexto
    ctx = app.app_context()
    ctx.push()  # 🔹 Activamos el contexto manualmente
    
    try:
        now = datetime.now(timezone.utc)
        print(f"Ejecutando check_pending_quizzes: {now}")

        # Accedemos a la sesión dentro del contexto
        pending_quizzes = db.session.execute(
            select(CompetitionQuiz)
            .where(and_(
                CompetitionQuiz.end_time <= now,
                CompetitionQuiz.processed == False  # noqa: E712
            ))
        ).scalars().all()
        print(f"Quizzes pendientes: {len(pending_quizzes)}")

        for quiz in pending_quizzes:
            CompetitionQuizService.process_quiz_results(quiz)

        db.session.commit()
    except Exception as e:
        print(f"Error en check_pending_quizzes: {e}")
        db.session.rollback()  # 🔹 Rollback ante errores
    finally:
        ctx.pop()  # 🔹 Liberamos el contexto

def start_scheduler(app: Flask):
    """Inicia el scheduler asegurando una única instancia."""
    if not hasattr(app, 'scheduler'):
        # Crea el scheduler y guárdalo en el objeto app
        app.scheduler = BackgroundScheduler()
        app.scheduler.add_job(
            check_pending_quizzes, 
            'interval', 
            seconds=20, 
            args=[app]  # 🔹 Pasamos la app como argumento
        )
        app.scheduler.start()
        print("Scheduler iniciado con éxito")