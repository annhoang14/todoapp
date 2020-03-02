from django.shortcuts import render, redirect, get_object_or_404
from django.views import generic
from .forms import EditToDoForm, AddToDoForm
from .models import ToDoItem
from django.views.generic.edit import CreateView, UpdateView
from django.utils import timezone
import datetime
from dateutil.relativedelta import relativedelta
from background_task import background
from django.core.mail import send_mail

class ToDoListView(generic.ListView):
    template_name = 'todo/todo_list.html'
    context_object_name = 'todo_list'

    def get_queryset(self):
        # update the priority twice a day if the due date is getting close
        # if datetime.datetime.utcnow().replace(tzinfo=timezone.utc).hour
        for item in ToDoItem.objects.all():
            timediff = (item.duedate - timezone.now()) / \
                datetime.timedelta(days=1)
            if timediff <= 1:
                item.priority = 'HI'
            elif timediff <= 2:
                item.priority = 'MD'
            else:
                item.priority = 'LO'
            item.save()
        check_notifications(repeat=10)
        return ToDoItem.objects.filter(completed=False).order_by('duedate')
#CANNOT CREATE A DIFFERENT PRIORITY

class CompletedView(generic.ListView):
    template_name = 'todo/todo_list.html'
    context_object_name = 'todo_list'

    def get_queryset(self):
        return ToDoItem.objects.filter(completed=True).order_by('duedate')


# https://docs.djangoproject.com/en/3.0/topics/class-based-views/generic-editing/
#allows adding new obj to database
class AddToDoItemView(CreateView):
    model = ToDoItem
    template_name = "todo/todoitem_form.html"
    form_class = AddToDoForm

    #set title and duedate fields to be required
    def get_form(self, form_class=None):
        form = super(AddToDoItemView, self).get_form(form_class)
        form.fields['title'].required = True
        form.fields['duedate'].required = True
        return form

    # overriding form_valid function to redirect to create_recurrences when add a todo item
    def form_valid(self, form):
        self.object = form.save()
        if (self.object.recur_freq != 'NEVER'):
            return redirect('todo_list:create_recurrences', todo_item_id=self.object.id)
        else:
            self.object.save()
            return redirect('todo_list:todo_list')

#function create recurrence of newly added objects based on recur_freq and end_recur_date fields
def create_recurrences(request, todo_item_id):
    todo_item = get_object_or_404(ToDoItem, pk=todo_item_id)  # get obj
    # if recur_freq is not NEVER
    if (todo_item.recur_freq != 'NEVER'):
        end_date = todo_item.end_recur_date  # get end_recur_date from current obj
        due_date = todo_item.duedate #get current duedate
        if (todo_item.recur_freq == 'DAILY'):
            delta = end_date - (due_date + relativedelta(days=+1)) # find the time differences
            delta_day = delta.days + 1
            for i in range(1, delta_day+1):
                ToDoItem.objects.create(
                    title=todo_item.title,
                    description=todo_item.description,
                    location=todo_item.location,
                    duedate=todo_item.duedate + relativedelta(days=+i),
                    recur_freq=todo_item.recur_freq,
                    end_recur_date=todo_item.end_recur_date,
                    priority=todo_item.priority
                    # completed = default False
                )

        elif (todo_item.recur_freq == 'WEEKLY'):
            delta = end_date - due_date # find the time differences
            delta_day = delta.days
            weeks = delta_day // 7  # number of weeks
            for i in range(1, weeks + 1):
                ToDoItem.objects.create(
                    title=todo_item.title,
                    description=todo_item.description,
                    location=todo_item.location,
                    duedate=todo_item.duedate + relativedelta(weeks=+i),
                    recur_freq=todo_item.recur_freq,
                    end_recur_date=todo_item.end_recur_date,
                    priority=todo_item.priority
                    # completed = default False
                )

        elif (todo_item.recur_freq == 'MONTHLY'):
            delta = end_date - due_date  # find the time differences
            DAYS_IN_YR = 365
            MONTHS_IN_YR = 12
            DAYS_IN_MONTHS = 30  # roughly
            delta_month = (delta.days // DAYS_IN_YR) * MONTHS_IN_YR
            # days left that's not a year
            delta_remainders = (delta.days % DAYS_IN_YR)
            months_leftover = delta_remainders // DAYS_IN_MONTHS

            for i in range(1, delta_month + months_leftover + 1):
                ToDoItem.objects.create(
                    title=todo_item.title,
                    description=todo_item.description,
                    location=todo_item.location,
                    duedate=todo_item.duedate + relativedelta(months=+i),
                    recur_freq=todo_item.recur_freq,
                    end_recur_date=todo_item.end_recur_date,
                    priority=todo_item.priority
                    # completed = default False
                )
        elif (todo_item.recur_freq == 'YEARLY'):
            delta_year = end_date.year - due_date.year  # find the time differences
            # loop thro day_dif to create and save that many obj
            for i in range(1, delta_year + 1):
                ToDoItem.objects.create(
                    title=todo_item.title,
                    description=todo_item.description,
                    location=todo_item.location,
                    duedate=todo_item.duedate + relativedelta(years=+i),
                    recur_freq=todo_item.recur_freq,
                    end_recur_date=todo_item.end_recur_date,
                    priority=todo_item.priority
                    # completed = default False
                )

    return redirect('todo_list:todo_list')

#view allows update/edit of object in database
class EditToDo(UpdateView):
    model = ToDoItem
    template_name = "todo/edit_todoitem_form.html"
    form_class = EditToDoForm

    # set title and duedate fields to be required
    def get_form(self, form_class=None):
        form = super(EditToDo, self).get_form(form_class)
        form.fields['title'].required = True
        form.fields['duedate'].required = True
        return form

    #override form_valid to check to see if recur_freq has changed
    #https://django-model-utils.readthedocs.io/en/latest/utilities.html#field-tracker
    def form_valid(self, form):
        has_freq_changed = self.object.tracker.has_changed('recur_freq') #returns true if recur_freq field has changed
        has_end_recur_date_changed = self.object.tracker.has_changed('end_recur_date') #returns true if end_recur_date has changed
        self.object = form.save() #save object to get new value of recur_freq
        if ( has_freq_changed or has_end_recur_date_changed ): #if either is True, edit recurrences
            return redirect('todo_list:edit_recurrences', todo_item_id=self.object.id)
        else:
            self.object.save()
            return redirect('todo_list:todo_list')

#function checks if user has edited recur_freq field and make according changes to all future tasks
def edit_recurrences(request, todo_item_id):
    todo_item = get_object_or_404(ToDoItem, pk=todo_item_id)  # get obj
    # for all changes, delete all future instances and remake others
    #https://docs.djangoproject.com/en/2.0/ref/models/querysets/
    ToDoItem.objects.filter(title__startswith = todo_item.title, #filter by title
                            duedate__gt=todo_item.duedate, #filter by duedate >= todo_item.title
                            ).delete()
    #redirect to create_recurrences to make new future instances
    return redirect('todo_list:create_recurrences', todo_item_id=todo_item_id)


def delete_todo(request, todo_item_id):
    item = ToDoItem.objects.get(pk=todo_item_id)
    item.delete()
    return redirect('todo_list:todo_list')


# function flips the completion status of a todo (T -> F ; F -> T)
def complete_todo(request, todo_item_id):
    # Todo item to be completed
    completedToDo = ToDoItem.objects.get(id=todo_item_id)
    completedToDo.completed = not completedToDo.completed
    completedToDo.save()

    return redirect('todo_list:todo_list')

# function flips the notify status of a todo (T -> F ; F -> T)
def notify_todo(request, todo_item_id):
    todo_item = ToDoItem.objects.get(id=todo_item_id)
    todo_item.notify = not todo_item.notify
    todo_item.save()

    return redirect('todo_list:todo_list')

#background process that runs every 30 minutes to check if any notifications need to be sent
#@background(schedule=1800)
#test which runs every 10 seconds
@background(schedule=10)
def check_notifications():
    todos_notify = ToDoItem.objects.filter(notify=True)
    if todos_notify:
        for todo in todos_notify:
            timediff = (todo.duedate - timezone.now()) / \
                datetime.timedelta(hours=1)
            if timediff <= 2 and timediff >= 1:
                notify_time = todo.duedate + relativedelta(hours=-1)
                notify_email(todo.id, schedule=notify_time)

@background
def notify_email(todo_item_id):
    todo_notify = ToDoItem.objects.get(id=todo_item_id)
    send_mail(
        todo_notify.title + ' due soon!',
        'Your todo item is due soon!' + 
        '\n Title: ' + todo_notify.title + 
        '\n Description: \t' + todo_notify.description +
        '\n Due: \t' + todo_notify.duedate.strftime("%m/%d/%Y, %H:%M:%S"),
        'personaldashboard.bogosorters@gmail.com',
        ['10myemail30@gmail.com'],
    )
    
