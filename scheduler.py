from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select, and_
from extensions import db
from app.models import CompetitionQuiz
from app.services import CompetitionQuizService

def check_pending_quizzes(app):
    """Verificación robusta de quizzes pendientes con gestión de contexto"""
    with app.app_context():
        try:
            print(f"⏰ Iniciando chequeo de quizzes pendientes ({datetime.now(timezone.utc)})")
            
            # Bloquear registros para procesamiento exclusivo (PostgreSQL/Mysql)
            pending = db.session.execute(
                select(CompetitionQuiz)
                .where(
                    CompetitionQuiz.end_time <= datetime.now(timezone.utc),
                    CompetitionQuiz.processed == False  # noqa: E712
                )
                .execution_options(stream_results=True)
                .with_for_update(skip_locked=True)  # Solo para bases que soportan SKIP LOCKED
            ).scalars().all()

            print(f"🔍 {len(pending)} quizzes pendientes encontrados")

            for quiz in pending:
                print(f"⚙️ Procesando quiz {quiz.id}")
                if CompetitionQuizService.process_quiz_results(quiz):
                    print(f"✅ Quiz {quiz.id} procesado exitosamente")
                else:
                    print(f"⚠️ Quiz {quiz.id} falló en procesamiento")

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            print(f"🚨 Error catastrófico en scheduler: {str(e)}")
            raise

def start_scheduler(app):
    """Inicialización segura del scheduler"""
    if not hasattr(app, 'scheduler'):
        scheduler = BackgroundScheduler(daemon=True)
        scheduler.add_job(
            lambda: check_pending_quizzes(app),
            'interval',
            # seconds=40,
            hours=1,
            max_instances=1,
            coalesce=True
        )
        scheduler.start()
        app.scheduler = scheduler
        print("🚀 Scheduler iniciado en modo seguro")