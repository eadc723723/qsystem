from celery import shared_task
from .models import Counter

@shared_task
def reset_counters():
    Counter.objects.all().update(status='offline')