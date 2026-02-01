import os
import django
from django.conf import settings

from core.tests.test_event_scheduling import SchedTestModel

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lex_app.settings')
django.setup()

from django.utils import timezone
from datetime import timedelta
from django_celery_beat.models import PeriodicTask

def reproduce():
    # 1. Create a record (Past)
    print("Creating initial record...")
    obj = SchedTestModel.objects.create(name="Repro")
    
    # 2. Get the history record
    hist = obj.history.first()
    print(f"Initial History: {hist.valid_from}")
    
    # 3. Update the history record to the FUTURE
    print("Updating history record to future...")
    future_time = timezone.now() + timedelta(hours=1)
    hist.valid_from = future_time
    hist.save() # This triggers post_save on HistoryModel, but maybe NOT trigger_meta_history?
    
    print(f"Updated History to: {hist.valid_from}")
    
    # 4. Check for Schedule
    # task name format: activate_{app}_{model}_{hist_id}...
    # We can just check count or filter by args
    
    tasks = PeriodicTask.objects.all()
    print(f"Total PeriodicTasks found: {len(tasks)}")
    found = False
    for t in tasks:
        print(f" - Task: {t.name} (Enabled: {t.enabled})")
        if "activate_history_version" in t.task:
             found = True
             
    if found:
        print("SUCCESS: Task was scheduled!")
    else:
        print("FAILURE: No task scheduled for updated history record.")

if __name__ == "__main__":
    try:
        reproduce()
    except Exception as e:
        print(f"Error: {e}")
