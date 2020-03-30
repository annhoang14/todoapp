from celery import shared_task
from celery.schedules import crontab

from django.utils import timezone
import datetime
import pytz
from dateutil.relativedelta import relativedelta
from django.core.mail import send_mail

from .models import ToDoItem

@shared_task
def notify_email(todo_item_id):
    todo_notify = ToDoItem.objects.get(id=todo_item_id)
    notify_time = todo_notify.duedate + relativedelta(hours=-1)
    queue_email.apply_async((todo_notify.id,), eta=notify_time)

@shared_task
def queue_email(todo_item_id):
    todo_notify = ToDoItem.objects.get(id=todo_item_id)
    due_date_local = todo_notify.duedate.astimezone(pytz.timezone("America/New_York"))
    send_mail(
        todo_notify.title + ' due soon!',
        'Your todo item is due soon!' + 
        '\n Title: ' + todo_notify.title + 
        '\n Description: \t' + todo_notify.description +
        '\n Due: \t' + due_date_local.strftime("%m/%d/%Y, %I:%M:%S %p"),
        'personaldashboard.bogosorters@gmail.com',
        ['10myemail30@gmail.com'],
   )