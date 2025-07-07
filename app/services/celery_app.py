import os
from celery import Celery

from dotenv import load_dotenv

load_dotenv()


celery_application = Celery("ecosystem-ai", 
                            broker=os.getenv("REDIS_BROKER_URL"),
                            backend=os.getenv("REDIS_BACKEND_URL"))

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
            'options': {'queue': 'app2_queue'}
        },
        "sending-mail": {
            'task': 'app.schedulars.email_generation.send_emails',
            'schedule': 10.00,
            'options': {'queue': 'app2_queue'}
        }
    }
)

celery_application.autodiscover_tasks(['app.schedulars.email_generation'])

