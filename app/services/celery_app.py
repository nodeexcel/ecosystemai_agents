from celery import Celery

celery_application = Celery("ecosystem-ai", 
                            )

celery_application.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    task_default_queue='app2_queue',
    beat_schedule={
        'add-every-10-seconds': {
            'task': 'app.services.tasks.add',
            'schedule': 10.0,
            'args': (1, 2),
        }
    }
)