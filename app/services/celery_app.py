from celery import Celery

celery_application = Celery("ecosystem-ai", 
                            broker="redis://localhost:6379/0",
                            backend="redis://localhost:6379/1")

celery_application.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    task_default_queue='app2_queue',
    beat_schedule={
        'creating-mail': {
            'task': 'app.schedulars.email_generation.create_emails',
            'schedule': 36.00,
        },
        "sending-mail": {
            'task': 'app.schedulars.email_generation.send_emails',
            'schedule': 10.00
        }
    }
)

celery_application.autodiscover_tasks(['app.schedulars.email_generation'])
