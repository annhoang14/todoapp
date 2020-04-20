from django.shortcuts import render, redirect, get_object_or_404
from django.views import generic
from .forms import ToDoForm, CourseForm, DayForm, ECForm, MonthForm, SubTaskModelFormSet, WeekForm
from .models import ToDoItem, Course, Extracurricular, Note, SubTask
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.dates import DayArchiveView, TodayArchiveView
from django.utils import timezone
import datetime
from datetime import date
import pytz
from dateutil.relativedelta import relativedelta
from django.http import HttpResponseRedirect
import calendar


######################## TO DO view ################################
# https://docs.djangoproject.com/en/3.0/topics/class-based-views/generic-editing/
# allows adding new obj to database
class AddToDoItemView(CreateView):
    model = ToDoItem
    template_name = "todo/todoitem_form.html"
    form_class = ToDoForm

    # set title and duedate fields to be required
    def get_form(self, form_class=None):
        form = super(AddToDoItemView, self).get_form(form_class)
        form.fields['end_recur_date'].required = True
        form.fields['course'].required = False
        form.fields['ec'].required = False
        return form

    # overriding form_valid function to redirect to create_recurrences when add a todo item
    def form_valid(self, form):
        object = form.save()
        object.user = self.request.user
        object.save()
        if (object.recur_freq != 'NEVER'):
            return redirect('todo_list:create_recurrences', todo_item_id=object.id)
        else:
            object.user = self.request.user
            object.save()
            return redirect('todo_list:todo_list')


# function create recurrence of newly added objects based on recur_freq and end_recur_date fields
def create_recurrences(request, todo_item_id):
    todo_item = get_object_or_404(ToDoItem, pk=todo_item_id)
    # if recur_freq is not NEVER
    if (todo_item.recur_freq != 'NEVER'):
        end_date = todo_item.end_recur_date  # get end_recur_date from current obj
        due_date = todo_item.duedate  # get current duedate
        if ( end_date < due_date ):
            return redirect('todo_list:todo_list')
        if (todo_item.recur_freq == 'DAILY'):
            # find the time differences
            delta = end_date - (due_date + relativedelta(days=+1))
            delta_day = delta.days + 1
            for i in range(1, delta_day + 1):
                ToDoItem.objects.create(
                    course=todo_item.course,
                    ec=todo_item.ec,
                    title=todo_item.title,
                    description=todo_item.description,
                    location=todo_item.location,
                    duedate=todo_item.duedate + relativedelta(days=+i),
                    recur_freq=todo_item.recur_freq,
                    end_recur_date=todo_item.end_recur_date,
                    priority=todo_item.priority,
                    category=todo_item.category,
                    user=request.user,
                    # progress default 0
                    # completed = default False
                )

        elif (todo_item.recur_freq == 'WEEKLY'):
            delta = end_date - due_date  # find the time differences
            delta_day = delta.days
            weeks = delta_day // 7  # number of weeks
            for i in range(1, weeks + 1):
                ToDoItem.objects.create(
                    course=todo_item.course,
                    ec=todo_item.ec,
                    title=todo_item.title,
                    description=todo_item.description,
                    location=todo_item.location,
                    duedate=todo_item.duedate + relativedelta(weeks=+i),
                    recur_freq=todo_item.recur_freq,
                    end_recur_date=todo_item.end_recur_date,
                    priority=todo_item.priority,
                    category=todo_item.category,
                    user=request.user,
                    # progress default 0
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
                    course=todo_item.course,
                    ec=todo_item.ec,
                    title=todo_item.title,
                    description=todo_item.description,
                    location=todo_item.location,
                    duedate=todo_item.duedate + relativedelta(months=+i),
                    recur_freq=todo_item.recur_freq,
                    end_recur_date=todo_item.end_recur_date,
                    priority=todo_item.priority,
                    category=todo_item.category,
                    user=request.user,
                    # progress default 0
                    # completed = default False
                )

        elif (todo_item.recur_freq == 'YEARLY'):
            # find the time differences
            delta_year = relativedelta(end_date, due_date).years
            # loop thro day_dif to create and save that many obj
            for i in range(1, delta_year + 1):
                ToDoItem.objects.create(
                    course=todo_item.course,
                    ec=todo_item.ec,
                    title=todo_item.title,
                    description=todo_item.description,
                    location=todo_item.location,
                    duedate=todo_item.duedate + relativedelta(years=+i),
                    recur_freq=todo_item.recur_freq,
                    end_recur_date=todo_item.end_recur_date,
                    priority=todo_item.priority,
                    category=todo_item.category,
                    user=request.user,
                    # progress default 0
                    # completed = default False
                )
    return redirect('todo_list:todo_list')


# view allows update/edit of object in database
class EditToDo(UpdateView):
    model = ToDoItem
    template_name = "todo/edit_todoitem_form.html"
    form_class = ToDoForm

    # set title and duedate fields to be required
    def get_form(self, form_class=None):
        form = super(EditToDo, self).get_form(form_class)
        form.fields['end_recur_date'].required = True
        form.fields['course'].required = False
        form.fields['ec'].required = False
        return form

    # override form_valid to check to see if recur_freq has changed
    # https://django-model-utils.readthedocs.io/en/latest/utilities.html#field-tracker
    def form_valid(self, form):
        todo = form.save(commit=False)
        if (self.request.POST.get("change-once")):  # only change fields for one instance
            todo.save()
            form.save_m2m()
            return redirect('todo_list:todo_list')
        # if changed for all future events and current instance
        elif (self.request.POST.get("change-all")):
            fields_changed = self.object.tracker.changed()
            if (len(fields_changed) == 0):
                todo.save()
                form.save_m2m()
                return redirect('todo_list:todo_list')
            else:
                todo.has_title_changed = self.object.tracker.has_changed(
                    'title')
                todo.has_description_changed = self.object.tracker.has_changed(
                    'description')
                todo.has_location_changed = self.object.tracker.has_changed(
                    'location')
                todo.has_category_changed = self.object.tracker.has_changed(
                    'category')
                todo.has_priority_changed = self.object.tracker.has_changed(
                    'priority')

                # date changes
                todo.has_duedate_changed = self.object.tracker.has_changed(
                    'duedate')
                todo.has_recur_freq_changed = self.object.tracker.has_changed(
                    'recur_freq')  # returns true if recur_freq field has changed
                todo.has_end_recur_date_changed = self.object.tracker.has_changed(
                    'end_recur_date')  # returns true if end_recur_date has changed

                # filter by fields that are likely to be changed together or least likely to change:
                # title, duedate, recur_freq, end_recur_date, category
                if (todo.has_title_changed):
                    titles = todo.tracker.previous('title')
                elif (not todo.has_title_changed):
                    titles = todo.title
                if (todo.has_duedate_changed):
                    duedates = todo.tracker.previous('duedate')
                else:
                    duedates = todo.duedate
                if (todo.has_recur_freq_changed):
                    recur_freqs = todo.tracker.previous('recur_freq')
                else:
                    recur_freqs = todo.recur_freq
                if (todo.has_end_recur_date_changed):
                    end_recur_dates = todo.tracker.previous('end_recur_date')
                else:
                    end_recur_dates = todo.end_recur_date
                if (todo.has_category_changed):
                    categories = todo.tracker.previous('category')
                else:
                    categories = todo.category

                future_events = ToDoItem.objects.filter(title=titles,
                                                        duedate__gt=duedates,
                                                        recur_freq=recur_freqs,
                                                        end_recur_date=end_recur_dates,
                                                        category=categories,
                                                        user=self.request.user,
                                                        )

                # filter how many of the same event that is in the future
                if (len(future_events) == 0):
                    todo.save()
                    form.save_m2m()
                    if (todo.has_end_recur_date_changed or todo.has_recur_freq_changed or todo.has_duedate_changed):
                        return redirect('todo_list:create_recurrences', todo_item_id=todo.id)
                    else:
                        return redirect('todo_list:todo_list')

                for future_event in future_events:
                    todo.future_events.append(future_event.id)
                # print( future_events )

                todo.save()
                form.save_m2m()

                return redirect('todo_list:change_all', todo_item_id=todo.id)


def change_all(request, todo_item_id):
    todo_item = get_object_or_404(ToDoItem, pk=todo_item_id)  # get obj

    for i in todo_item.future_events:
        future_event = ToDoItem.objects.get(pk=i)
        if (todo_item.has_title_changed):
            future_event.title = todo_item.title
        if (todo_item.has_description_changed):
            future_event.description = todo_item.description
        if (todo_item.has_location_changed):
            future_event.location = todo_item.location
        if (todo_item.has_category_changed):
            future_event.category = todo_item.category
        if (todo_item.has_priority_changed):
            future_event.priority = todo_item.priority
        future_event.course = todo_item.course
        future_event.ec = todo_item.ec
        future_event.save()

    todo_item.has_title_changed = False
    todo_item.has_description_changed = False
    todo_item.has_location_changed = False
    todo_item.has_category_changed = False
    todo_item.has_priority_changed = False
    todo_item.save()

    if (todo_item.has_end_recur_date_changed or todo_item.has_recur_freq_changed or todo_item.has_duedate_changed):
        return redirect('todo_list:edit_recurrences', todo_item_id=todo_item_id)

    else:
        todo_item.future_events = []
        todo_item.save()
        return redirect('todo_list:todo_list')

# function checks if user has edited recur_freq field and make according changes to all future tasks


def edit_recurrences(request, todo_item_id):
    todo_item = get_object_or_404(ToDoItem, pk=todo_item_id)  # get obj
    # for date changes, delete all future instances and remake others
    # https://docs.djangoproject.com/en/2.0/ref/models/querysets/
    for i in todo_item.future_events:
        ToDoItem.objects.get(pk=i).delete()

    todo_item.has_end_recur_date_changed = False
    todo_item.has_recur_freq_changed = False
    todo_item.has_duedate_changed = False
    todo_item.future_events = []
    todo_item.save()
    # redirect to create_recurrences to make new future instances
    return redirect('todo_list:create_recurrences', todo_item_id=todo_item_id)


# https://medium.com/all-about-django/adding-forms-dynamically-to-a-django-formset-375f1090c2b0
# function creates subtask with formset; creating multiple subtasks on the same page
def create_subtask_model_form(request, todo_item_id):
    template_name = 'todo/add_subtask_form.html'
    if request.method == 'POST':
        formset = SubTaskModelFormSet(request.POST)
        if formset.is_valid():
            for form in formset:
                if form.cleaned_data.get('detail'):
                    obj = form.save()
                    obj.todo = ToDoItem.objects.get(
                        id=todo_item_id, user=request.user)
                    obj.user = request.user
                    obj.save()
                    form.save()
            return redirect('todo_list:todo_list')
    else:
        formset = SubTaskModelFormSet(queryset=SubTask.objects.none())
    return render(request, template_name, {
        'formset': formset,
        'todo_item': ToDoItem.objects.get(id=todo_item_id, user=request.user)
    })

# subtask is crossed out when completed, but not gone


def complete_subtask(request, subtask_id):
    completedSubTask = SubTask.objects.get(id=subtask_id, user=request.user)
    completedSubTask.completed = not completedSubTask.completed
    completedSubTask.save()
    return redirect(request.META.get('HTTP_REFERER', '/'))


class ToDoListView(generic.ListView):
    template_name = 'todo/todo_list.html'
    context_object_name = 'todo_list'

    def get_context_data(self, **kwargs):
        context = super(ToDoListView, self).get_context_data(**kwargs)
        user_note = None
        try:
            user_note = Note.objects.get(user=self.request.user)
        except Note.DoesNotExist:
            user_note = Note.objects.create(user=self.request.user, text='')
        context['note'] = user_note.text
        return context

    def get_queryset(self):
        # update the priority twice a day if the due date is getting close
        # if datetime.datetime.utcnow().replace(tzinfo=timezone.utc).hour
        items = ToDoItem.objects.all()
        if self.request.user.is_authenticated:
            items = ToDoItem.objects.filter(user=self.request.user)

        for item in items:
            daydiff = (item.duedate - timezone.now()) / \
                datetime.timedelta(days=1)
            if daydiff <= 1:
                item.priority = 'HI'
            elif daydiff <= 2 and item.priority != 'HI':
                item.priority = 'MD'
            item.save()

        if not self.request.user.is_authenticated:
            return ToDoItem.objects.filter(completed=False).order_by('duedate')
        return ToDoItem.objects.filter(completed=False, user=self.request.user).order_by('duedate')

    def get(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            # redirect to login if user isn't logged in
            return redirect("/login/")
        return super(ToDoListView, self).get(*args, **kwargs)


def save_notes(request):
    if request.method == 'POST':
        user = request.user
        text = request.POST.get('notes', '')
        print(user, user.id, text)
        user_note = None
        try:
            user_note = Note.objects.get(user=user)
        except Note.DoesNotExist:
            user_note = Note.objects.create(user=user, text='')
        user_note.text = text
        user_note.save()
        return redirect('todo_list:todo_list')


class CompletedView(generic.ListView):
    template_name = 'todo/completed_list.html'
    context_object_name = 'todo_list'

    def get_queryset(self):
        return ToDoItem.objects.filter(completed=True, user=self.request.user).order_by('duedate')

    def get(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            # redirect to login if user isn't logged in
            return redirect("/login/")
        return super(CompletedView, self).get(*args, **kwargs)


def delete_todo(request, todo_item_id):
    item = ToDoItem.objects.get(pk=todo_item_id, user=request.user)
    item.delete()
    return redirect('todo_list:todo_list')


# function flips the completion status of a todo (T -> F ; F -> T)
def complete_todo(request, todo_item_id):
    # Todo item to be completed
    completedToDo = ToDoItem.objects.get(id=todo_item_id, user=request.user)
    completedToDo.completed = not completedToDo.completed
    completedToDo.progress = 100
    completedToDo.save()

    return redirect(request.META.get('HTTP_REFERER', '/'))


def delete_all_completed(request):
    ToDoItem.objects.filter(completed=True, user=request.user).delete()
    return redirect('todo_list:completed')


def delete_all_incompleted(request):
    ToDoItem.objects.filter(completed=False, user=request.user).delete()
    return redirect('todo_list:todo_list')

##################################################################


class DayView(generic.FormView):
    template_name = 'todo/day_form.html'
    context_object_name = 'todo_list'
    form_class = DayForm

    def get_queryset(self):
        # https://stackoverflow.com/questions/4668619/how-do-i-filter-query-objects-by-date-range-in-django used for filter
        return ToDoItem.objects.filter(user=self.request.user).order_by('duedate')

    def form_valid(self, form):
        # return redirect('todo_list:create_recurrences', todo_item_id=self.object.id)
        url = str(form)
        return HttpResponseRedirect(url)

    def get(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            # redirect to login if user isn't logged in
            return redirect("/login/")
        return super(DayView, self).get(*args, **kwargs)


# https://docs.djangoproject.com/en/3.0/ref/class-based-views/generic-date-based/#dayarchiveview
class SpecificDayView(generic.DayArchiveView):
    template_name = 'todoitem_archive_day.html'
    #queryset = ToDoItem.objects.filter(completed=False).order_by('duedate')
    date_field = "duedate"
    ordering = 'duedate'
    allow_future = True
    allow_empty = True

    def get_queryset(self):
        return ToDoItem.objects.filter(completed=False, user=self.request.user).order_by('duedate')

    def get(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            # redirect to login if user isn't logged in
            return redirect("/login/")
        return super(SpecificDayView, self).get(*args, **kwargs)


class TodoTodayArchiveView(generic.TodayArchiveView):
    template_name = 'todoitem_archive_day.html'
    date_field = "duedate"
    ordering = 'duedate'
    allow_future = True
    allow_empty = True

    def get_queryset(self):
        return ToDoItem.objects.filter(completed=False, user=self.request.user).order_by('duedate')

    def get(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            # redirect to login if user isn't logged in
            return redirect("/login/")
        return super(TodoTodayArchiveView, self).get(*args, **kwargs)


class WeekView(generic.FormView):
    template_name = 'todo/week_form.html'
    context_object_name = 'todo_list'
    form_class = WeekForm

    today = date.today()

    def get_queryset(self):
        return ToDoItem.objects.filter(completed=False, user=self.request.user).order_by('duedate')

    def get(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            # redirect to login if user isn't logged in
            return redirect("/login/")
        return super(WeekView, self).get(*args, **kwargs)


class SpecificWeekView(generic.WeekArchiveView):
    template_name = 'todoitem_archive_week.html'
    date_field = "duedate"
    ordering = 'duedate'
    allow_future = True
    allow_empty = True

    def get_queryset(self):
        return ToDoItem.objects.filter(completed=False, user=self.request.user).order_by('duedate')

    def get(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            # redirect to login if user isn't logged in
            return redirect("/login/")
        return super(SpecificWeekView, self).get(*args, **kwargs)


class MonthView(generic.FormView):
    template_name = 'todo/month_form.html'
    context_object_name = 'todo_list'
    form_class = MonthForm

    def get_queryset(self):
        return ToDoItem.objects.filter(user=self.request.user).order_by('duedate')

    def form_valid(self, form):
        url = str(form)
        return HttpResponseRedirect(url)

    def get(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect("/login/")
        return super(MonthView, self).get(*args, **kwargs)


# class SpecificMonthView(generic.MonthArchiveView):
#     template_name = 'todoitem_archive_month.html'
#     queryset = ToDoItem.objects.filter(completed=False).order_by('duedate')
#     date_field = "duedate"
#     ordering = "duedate"
#     allow_future = True
#     allow_empty = True

def month_calendar_view(request, year, month):
    month_num = 0
    for abbr in calendar.month_abbr:
        if month == abbr:
            break
        month_num += 1
    calendar.setfirstweekday(calendar.SUNDAY)
    month_matrix = calendar.monthcalendar(year, month_num)

    class CalendarDay:
        def __init__(self, date, date_todo_list, blank, size):
            self.date = date
            self.date_todo_list = date_todo_list
            self.blank = blank
            self.size = size

        def __repr__(self):
            return str(self)

        def __str__(self):
            return "Calendar Day: " + str(self.date) + "\tTodos: " + str(self.date_todo_list) + "\tBlank: " + str(self.blank) + "\tSize: " + str(self.size)
    calendar_day_list = []
    for week_index in range(len(month_matrix)):
        calendar_day_list.append([])
        for day_index in range(7):
            day_date = month_matrix[week_index][day_index]
            if day_date == 0:
                calendar_day_list[week_index].append(
                    CalendarDay(day_date, [], True, 0))
            else:
                day_datetime = datetime.date(year, month_num, day_date)
                day_date_todos = ToDoItem.objects.filter(user=request.user, completed=False).exclude(
                    duedate__lt=day_datetime).exclude(duedate__gt=day_datetime+datetime.timedelta(days=1))
                day_size = int(len(day_date_todos)/4)
                if len(day_date_todos) == 0:
                    calendar_day_list[week_index].append(
                        CalendarDay(day_date, day_date_todos, False, -1))
                else:
                    calendar_day_list[week_index].append(
                        CalendarDay(day_date, day_date_todos, False, day_size))
    template_name = 'todo/calendar_month.html'
    return render(request, template_name, {
        'calendar_day_list': calendar_day_list,
        'month_name': calendar.month_name[month_num],
        'curr_year': year,
        'curr_month': month,
    })


def month_calendar_prev(request, year, month):
    month_names = ["Jan", "Feb", "Mar", "Apr", "May",
                   "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    new_year = year
    new_month = month
    if(month == "Jan"):
        new_year -= 1
        new_month = "Dec"
    else:
        new_month = month_names[month_names.index(month)-1]
    return redirect('todo_list:specific_month', year=new_year, month=new_month)


def month_calendar_next(request, year, month):
    month_names = ["Jan", "Feb", "Mar", "Apr", "May",
                   "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    new_year = year
    new_month = month
    if(month == "Dec"):
        new_year += 1
        new_month = "Jan"
    else:
        new_month = month_names[month_names.index(month)+1]
    return redirect('todo_list:specific_month', year=new_year, month=new_month)

    def get_queryset(self):
        return ToDoItem.objects.filter(completed=False, user=self.request.user).order_by('duedate')

    def get(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            # redirect to login if user isn't logged in
            return redirect("/login/")
        return super(SpecificMonthView, self).get(*args, **kwargs)


################ Course view ###########################

# add a course instance
class AddCourseView(CreateView):
    model = Course
    template_name = "todo/add_course_form.html"
    form_class = CourseForm


    def get_form(self, form_class=None):
        form = super(AddCourseView, self).get_form(form_class)
        form.fields['course_abbrev'].required = False
        form.fields['course_prof'].required = False
        return form

    def form_valid(self, form):
        self.object = form.save()
        self.object.user = self.request.user
        self.object.save()
        return redirect('todo_list:course_list')

#edit course
class EditCourseView(UpdateView):
    model = Course
    template_name = "todo/edit_course_form.html"
    form_class = CourseForm


    def get_form(self, form_class=None):
        form = super(EditCourseView, self).get_form(form_class)
        form.fields['course_abbrev'].required = False
        form.fields['course_prof'].required = False
        return form

    def form_valid(self, form):
        self.object = form.save()
        self.object.save()
        return redirect('todo_list:course_list')

# list for filter courses/academics
class CourseListView(generic.ListView):
    template_name = 'todo/course_list.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        return Course.objects.filter(user=self.request.user).order_by('course_name')

    def get(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            # redirect to login if user isn't logged in
            return redirect("/login/")
        return super(CourseListView, self).get(*args, **kwargs)


def delete_course(request, course_id):
    course = Course.objects.get(pk=course_id)
    course.delete()
    return redirect('todo_list:course_list')

################ Academics View ######################

# list Academics for "My academics" view
class AcademicsListView(generic.ListView):
    template_name = 'todo/academics_list.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        # update the priority twice a day if the due date is getting close
        # if datetime.datetime.utcnow().replace(tzinfo=timezone.utc).hour
        return Course.objects.filter(user=self.request.user).order_by('course_name')

        # https://docs.djangoproject.com/en/3.0/topics/class-based-views/generic-display/

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['no_course_todo_list'] = ToDoItem.objects.filter(
            category='AC', course=None, user=self.request.user)
        return context

    def get(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            # redirect to login if user isn't logged in
            return redirect("/login/")
        return super(AcademicsListView, self).get(*args, **kwargs)

#filter to-do item by Category and duedate = today
class AcademicsListTodayView(generic.ListView):
    template_name = 'todo/academics_today_list.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        # update the priority twice a day if the due date is getting close
        # if datetime.datetime.utcnow().replace(tzinfo=timezone.utc).hour
        return Course.objects.filter(user=self.request.user).order_by('course_name')

        # https://docs.djangoproject.com/en/3.0/topics/class-based-views/generic-display/

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['no_course_todo_list'] = ToDoItem.objects.filter(
            category='AC', course=None, user=self.request.user)
        return context

    def get(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            # redirect to login if user isn't logged in
            return redirect("/login/")
        return super(AcademicsListTodayView, self).get(*args, **kwargs)

######################### Extracurricular list view ####################################

# for filter EC view
class ECToDoList(generic.ListView):
    template_name = 'todo/ec_todo_list.html'
    context_object_name = 'ec_list'

    def get_queryset(self):
        # get list of ec ordered by name
        return Extracurricular.objects.filter(user=self.request.user).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # add list objects without a specific ec object but is categorized as ec
        context['no_ec_todo_list'] = ToDoItem.objects.filter(
            category='EC', ec=None, user=self.request.user)
        return context

    def get(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            # redirect to login if user isn't logged in
            return redirect("/login/")
        return super(ECToDoList, self).get(*args, **kwargs)

#filter to-do by Category EC and duedate = today
class ECTodayList( generic.ListView ):
    template_name = 'todo/ec_today_todo_list.html'
    context_object_name = 'ec_list'

    def get_queryset(self):
        # update the priority twice a day if the due date is getting close
        # if datetime.datetime.utcnow().replace(tzinfo=timezone.utc).hour
        return Extracurricular.objects.filter(user=self.request.user).order_by('name')

        # https://docs.djangoproject.com/en/3.0/topics/class-based-views/generic-display/

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['no_ec_todo_list'] = ToDoItem.objects.filter(
            category='EC', course=None, user=self.request.user)
        return context

    def get(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            # redirect to login if user isn't logged in
            return redirect("/login/")
        return super(ECTodayList, self).get(*args, **kwargs)


# create an EC instance
class AddEC(CreateView):
    model = Extracurricular
    template_name = "todo/add_ec_form.html"
    form_class = ECForm

    # set title and duedate fields to be required
    def get_form(self, form_class=None):
        form = super(AddEC, self).get_form(form_class)
        form.fields['detail'].required = False
        form.fields['start_date'].required = False
        form.fields['end_date'].required = False
        return form

    # overriding form_valid function to redirect to create_recurrences when add a todo item
    def form_valid(self, form):
        self.object = form.save()
        self.object.user = self.request.user
        self.object.save()
        return redirect('todo_list:ec_list')

# edit EC instance
class EditEC(UpdateView):
    model = Extracurricular
    template_name = "todo/edit_ec_form.html"
    form_class = ECForm

    # set title and duedate fields to be required
    def get_form(self, form_class=None):
        form = super(EditEC, self).get_form(form_class)
        form.fields['detail'].required = False
        form.fields['start_date'].required = False
        form.fields['end_date'].required = False
        form.fields['active'].required = False
        return form

    def form_valid(self, form):
        self.object = form.save()
        self.object.save()
        return redirect('todo_list:ec_list')


# purely EC list view for "My Extracurriculars" view
class ECListView(generic.ListView):
    template_name = 'todo/ec_list.html'
    context_object_name = 'ec_list'

    def get_queryset(self):
        return Extracurricular.objects.filter(user=self.request.user).order_by('name')

    def get(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            # redirect to login if user isn't logged in
            return redirect("/login/")
        return super(ECListView, self).get(*args, **kwargs)


def delete_ec(request, ec_id):
    ec = Extracurricular.objects.get(pk=ec_id)
    ec.delete()
    return redirect('todo_list:ec_list')


################################### Job View ##########################################
class JobListView(generic.ListView):
    template_name = 'todo/job_list.html'
    context_object_name = 'todo_list'

    def get_queryset(self):
        # update the priority twice a day if the due date is getting close
        # if datetime.datetime.utcnow().replace(tzinfo=timezone.utc).hour
        for item in ToDoItem.objects.filter(user=self.request.user):
            timediff = (item.duedate - timezone.now()) / \
                datetime.timedelta(days=1)
            if timediff <= 1:
                item.priority = 'HI'
            elif timediff <= 2:
                item.priority = 'MD'
            else:
                item.priority = 'LO'
            item.save()
        return ToDoItem.objects.filter(completed=False, category='JB', user=self.request.user).order_by('duedate')

    def get(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            # redirect to login if user isn't logged in
            return redirect("/login/")
        return super(JobListView, self).get(*args, **kwargs)

#filter by Job and duedate=today
class JobTodayList( generic.ListView ):
    template_name = 'todo/job_today_todo_list.html'
    context_object_name = 'todo_list'

    def get_queryset(self):
        now = timezone.now()
        return ToDoItem.objects.filter(duedate__year = now.year,
                                       duedate__month = now.month,
                                       duedate__day = now.day,
                                       completed=False,
                                       category='JB',
                                       user=self.request.user).order_by('duedate')


        # https://docs.djangoproject.com/en/3.0/topics/class-based-views/generic-display/

    def get(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            # redirect to login if user isn't logged in
            return redirect("/login/")
        return super(JobTodayList, self).get(*args, **kwargs)

############### Social View ###################


class SocialListView(generic.ListView):
    template_name = 'todo/social_list.html'
    context_object_name = 'todo_list'

    def get_queryset(self):
        return ToDoItem.objects.filter(completed=False, category='SC', user=self.request.user).order_by('duedate')

class SocTodayList( generic.ListView ):
    template_name = 'todo/social_today_todo_list.html'
    context_object_name = 'todo_list'

    def get_queryset(self):
        now = timezone.now()
        return ToDoItem.objects.filter(duedate__year = now.year,
                                       duedate__month = now.month,
                                       duedate__day = now.day,
                                       completed=False,
                                       category='SC',
                                       user=self.request.user).order_by('duedate')


        # https://docs.djangoproject.com/en/3.0/topics/class-based-views/generic-display/

    def get(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            # redirect to login if user isn't logged in
            return redirect("/login/")
        return super(SocTodayList, self).get(*args, **kwargs)

###############################################################################


class PersonalListView(generic.ListView):
    template_name = 'todo/personal_list.html'
    context_object_name = 'todo_list'

    def get_queryset(self):
        return ToDoItem.objects.filter(completed=False, category='PS', user=self.request.user).order_by('duedate')

    def get(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            # redirect to login if user isn't logged in
            return redirect("/login/")
        return super(PersonalListView, self).get(*args, **kwargs)

class PersonalTodayList( generic.ListView ):
    template_name = 'todo/personal_today_todo_list.html'
    context_object_name = 'todo_list'

    def get_queryset(self):
        now = timezone.now()
        return ToDoItem.objects.filter(duedate__year = now.year,
                                       duedate__month = now.month,
                                       duedate__day = now.day,
                                       completed=False,
                                       category='PS',
                                       user=self.request.user).order_by('duedate')


        # https://docs.djangoproject.com/en/3.0/topics/class-based-views/generic-display/

    def get(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            # redirect to login if user isn't logged in
            return redirect("/login/")
        return super(PersonalTodayList, self).get(*args, **kwargs)


###########################################################################


class OtherListView(generic.ListView):
    template_name = 'todo/other_list.html'
    context_object_name = 'todo_list'

    def get_queryset(self):
        return ToDoItem.objects.filter(completed=False, category='OT', user=self.request.user).order_by('duedate')

    def get(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            # redirect to login if user isn't logged in
            return redirect("/login/")
        return super(OtherListView, self).get(*args, **kwargs)

class OtherTodayList( generic.ListView ):
    template_name = 'todo/other_today_todo_list.html'
    context_object_name = 'todo_list'

    def get_queryset(self):
        now = timezone.now()
        return ToDoItem.objects.filter(duedate__year = now.year,
                                       duedate__month = now.month,
                                       duedate__day = now.day,
                                       completed=False,
                                       category='OT',
                                       user=self.request.user).order_by('duedate')


        # https://docs.djangoproject.com/en/3.0/topics/class-based-views/generic-display/

    def get(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            # redirect to login if user isn't logged in
            return redirect("/login/")
        return super(OtherTodayList, self).get(*args, **kwargs)

# https://stackoverflow.com/questions/15566999/how-to-show-form-input-fields-based-on-select-value
