from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from fastapi_pundra.common.scheduler.schedule import bind_beat_schedule
from importlib import import_module
from dotenv import load_dotenv

load_dotenv()

def create_celery_app(project_name: str, broker_type: str = 'redis'):
  # Get project base path from environment
  project_base_path = os.getenv('PROJECT_BASE_PATH', 'app')
  
  # Dynamically import schedules based on PROJECT_BASE_PATH
  schedules_module = import_module(f'{project_base_path}.config.scheduler')
  schedules = schedules_module.schedules

  app = Celery(project_name)
  app.conf.update(
    broker_url=os.getenv('CELERY_BROKER_URL'),
    result_backend=os.getenv('CELERY_RESULT_BACKEND'),
    timezone='UTC',
    enable_utc=True,
  )

  if broker_type == 'redis':
    app.conf.beat_scheduler = 'redbeat.RedBeatScheduler'
    app.conf.redbeat_redis_url = os.getenv('CELERY_BROKER_URL')

  # Define default task modules that should always be included
  default_task_modules = [
    'fastapi_pundra.common.mailer.task'
  ]
  
  # Define project-specific task modules
  project_task_modules = [
    f"{project_base_path}.tasks"
  ]
  
  # Combine all task modules
  all_task_modules = project_task_modules + default_task_modules
  app.autodiscover_tasks(all_task_modules)

  app.conf.beat_schedule = bind_beat_schedule(schedules=schedules) 

  return app