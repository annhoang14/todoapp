from django.test import TestCase, Client
from .models import ToDoItem, Course
from .forms import ToDoForm
from django.utils import timezone
from django.urls import reverse
import pytz
import datetime
from dateutil.relativedelta import relativedelta

#https://developer.mozilla.org/en-US/docs/Learn/Server-side/Django/Testing
#https://docs.djangoproject.com/en/3.0/topics/testing/tools/
#https://stackoverflow.com/questions/18622007/runtimewarning-datetimefield-received-a-naive-datetime

#Note from Ann: make sure you create a course called "Tester" or something in every setUp()
    # look at my examples for details

def create_todo(new_title, #only need to provide title if none of the other fields change
                new_description='',
                new_location='',
                new_duedate=timezone.now(),
                new_priority='LO',
                new_completed=False,
                new_recur_freq='NEVER',
                new_end_recur_date=timezone.now(),
                new_category='NN',
                new_course=None,
                ):
    form_data = {'title':new_title,
        'description': new_description,
        'location':new_location,
        'duedate':new_duedate,
        'priority':new_priority,
        'completed':new_completed,
        'recur_freq':new_recur_freq,
        'end_recur_date':new_end_recur_date,
        'category': new_category,
        'course':new_course}

    form = ToDoForm(data=form_data)
    return form.save()

#if there is a dictionary of fields already available, use this function with the dictionary as parameter
def create_from_data_dict( form_data ):
    form = ToDoForm(data = form_data)
    return form.save()

#function to create a Course object
def create_course(
        new_course_name = 'Tester',
        new_course_abbrev ="",
        new_course_prof = "",
):
    return Course.objects.create(
        course_name = new_course_name,
        course_abbrev = new_course_abbrev,
        course_prof = new_course_prof
    )

class PriorityTest(TestCase):
    def setUp(self):
        self.my_course = create_course(
            new_course_name="Tester"
        )

        create_todo(
            new_title="priority test",
            new_priority="HI",
            new_duedate=datetime.datetime(2020, 2, 27, 8, 0, 0, tzinfo=pytz.utc),
            new_course=self.my_course
        )

    def test_check_priority(self):
        response = self.client.get(reverse('todo_list:todo_list'))
        l = response.context['todo_list']
        todo = l[0] #only item in list
        self.assertEqual(todo.title, "priority test")
        self.assertEqual(todo.priority, "HI")


class ToDoItemModelTests(TestCase):
    def test_same_is_today_duedate(self):
        """
       returns True if the duedate is the same as currentdate time
        """
        # create a new obj
        #naive = parse_datetime("2020-03-15 10:28:45")
        #pytz.timezone("America/New_York").localize(naive, is_dst=None)
        todo = ToDoItem(
            title="Test case 1",
            description="Testing is_today_duedate",
            duedate=datetime.datetime(2020, 3, 15, 6, 0, 0, tzinfo=pytz.utc)
        )

        day_dif = todo.is_today_duedate()
        self.assertIs(day_dif, False)


# write tests for day view: make sure that only tasks that are due on a certain day are shown


class ToDoItemFormTest(TestCase):
    """
    Test whether CreateView is successful
    """
    def setUp(self):
        self.my_course = create_course(
            new_course_name="Tester"
        )

        #this data will be passed into the Forms and create/update object
        self.data_form = {
            'title': "TBD",
            'description': '',
            'duedate': timezone.now(),
            'location': '',
            'recur_freq': 'NEVER',
            'end_recur_date': timezone.now(),
            'priority': 'LO',
            'category': 'NN',
            'course': self.my_course.id}

    def test_todoitemform_success_submission(self):
        self.data_form['title'] = 'Test submission success'
        form = ToDoForm(data=self.data_form)
        self.assertTrue(form.is_valid())

    def test_correct_template_for_add_todo(self):
        self.data_form['title'] = "Test correct template used"
        response = self.client.post( reverse('todo_list:add_todo_item'),self.data_form )
        self.assertEqual(response.status_code, 200)

        #make sure that add todo form is used
        self.assertTemplateUsed(response, 'todo/todoitem_form.html')

    def tearDown(self):
        del self.my_course
        del self.data_form

class CreateDailyRecurrencesTest(TestCase):
    def setUp(self):
        self.my_course = create_course(
            new_course_name="Tester"
        )
        self.data_form = {
            'title': "TBD",
            'description': '',
            'duedate': datetime.datetime(2020, 3, 16, 5, 0, 0, tzinfo=pytz.utc),
            'location': '',
            'recur_freq': 'DAILY',
            'end_recur_date': datetime.datetime(2020, 3, 16, 5, 0, 0, tzinfo=pytz.utc),
            'priority': 'LO',
            'category': 'NN',
            'course': self.my_course.id}

    def test_create_daily_recurrences_equiv(self):# equivalence test
        """
        Tests whether create_recurrenes work
        """
        self.data_form['title'] = "Test creating daily recurrences"
        self.data_form['description'] = "Some end_recur_date at the same time"
        self.data_form['end_recur_date'] = datetime.datetime(2020, 3, 19, 5, 0, 0, tzinfo=pytz.utc)

        daily_occurrence = create_from_data_dict(self.data_form) #create first instance

        #should create 4 instances
        self.client.post(reverse('todo_list:create_recurrences', kwargs={'todo_item_id': daily_occurrence.id}), self.data_form)
        current_query_set = ToDoItem.objects.all()
        self.assertEqual( 4, len(current_query_set))

        #check crucial fields
        filtered = ToDoItem.objects.filter(title='Test creating daily recurrences',
                                           description = "Some end_recur_date at the same time",
                                            recur_freq='DAILY',
                                              end_recur_date=datetime.datetime(2020, 3, 19, 5, 0, 0, tzinfo=pytz.utc))
        self.assertEqual(4, len(filtered))

        count_true = 0
        #check due date
        for i in range( len(filtered) - 1):
            if filtered[i].duedate == filtered[i+1].duedate - datetime.timedelta(days=1):
                count_true += 1

        #count_true has to be 3 because 3 comparisons if test works
        self.assertEqual(3, count_true )

    def test_redirect_from_create_recurrences_to_todo_list(self):
        """
        Test that after a successful create_recurrences, it redirects to todo_list
        """
        self.data_form['title'] = "Test redirect to list after creating_recurrences"
        self.data_form['recur_freq'] = 'DAILY'
        self.data_form['end_recur_date'] = datetime.datetime(2020, 3, 31, 5, 0, 0, tzinfo=pytz.utc)
        daily_occurrence = create_from_data_dict(self.data_form)

        response = self.client.post(
            reverse('todo_list:create_recurrences', kwargs={'todo_item_id': daily_occurrence.id}), self.data_form)
        self.assertRedirects(response, reverse('todo_list:todo_list'))

    def test_create_daily_recurrences_shorter_time(self):# boundary test
        """
        Some end_recur_date not a full day from duedate
        """
        self.data_form['title'] = "Test creating daily recurrences"
        self.data_form['description'] = "Some end_recur_date but with an earlier time than duedate"
        self.data_form['end_recur_date'] = datetime.datetime(2020, 3, 19, 4, 0, 0, tzinfo=pytz.utc)

        daily_occurrence = create_from_data_dict(self.data_form) #create first instance

        #should create 3 instances
        self.client.post(reverse('todo_list:create_recurrences', kwargs={'todo_item_id': daily_occurrence.id}), self.data_form)
        current_query_set = ToDoItem.objects.all()
        self.assertEqual( 3, len(current_query_set))

        #check crucial fields
        filtered = ToDoItem.objects.filter(title='Test creating daily recurrences',
                                         description="Some end_recur_date but with an earlier time than duedate",
                                         recur_freq='DAILY',
                                         end_recur_date=datetime.datetime(2020, 3, 19, 4, 0, 0, tzinfo=pytz.utc))
        self.assertEqual( 3, len(filtered))

        #check duedates of all 3 objects
        count_true = 0
        for i in range(len(filtered) - 1):
            if filtered[i].duedate == filtered[i + 1].duedate - datetime.timedelta(days=1):
                count_true += 1

        # count_true has to be 2 because 2 comparisons if test works
        self.assertEqual(2, count_true)


    def test_end_date_earlier_than_duedate(self):
        """
        Create end_recur_date earlier than duedate --> should create only one instance
        """
        self.data_form['title'] = "Test creating daily recurrences"
        self.data_form['description'] = "Some end_recur_date earlier than duedate"
        self.data_form['end_recur_date'] = datetime.datetime(2020, 3, 14, 4, 0, 0, tzinfo=pytz.utc)

        daily_occurrence = create_from_data_dict(self.data_form) #create first instance
        #should create 1 instance
        self.client.post(reverse('todo_list:create_recurrences', kwargs={'todo_item_id': daily_occurrence.id}), self.data_form)
        current_instance = ToDoItem.objects.get(description="Some end_recur_date earlier than duedate")
        all_instances = [current_instance]

        self.assertEqual( 1, len(all_instances))

        #check crucial fields
        one_instance = ToDoItem.objects.get(title ="Test creating daily recurrences",
                                         description="Some end_recur_date earlier than duedate",
                                         end_recur_date=datetime.datetime(2020, 3, 14, 4, 0, 0, tzinfo=pytz.utc))

        #check duedates of all 1 object
        self.assertEqual( one_instance.duedate, datetime.datetime(2020, 3, 16, 5, 0, 0, tzinfo=pytz.utc))

    def tearDown(self):
        del self.my_course
        del self.data_form

class CreateWeeklyRecurrencesTests(TestCase):
    def setUp(self):
        self.my_course = create_course(
            new_course_name="Tester"
        )

        # this data will be passed into the Forms and create/update object
        self.data_form = {
            'title': "Test creating weekly recurrences equivalence",
            'description': '',
            'duedate': datetime.datetime(2020, 3, 16, 5, 0, 0, tzinfo=pytz.utc),
            'location': '',
            'recur_freq': 'WEEKLY',
            'end_recur_date': datetime.datetime(2020, 3, 16, 5, 0, 0, tzinfo=pytz.utc),
            'priority': 'LO',
            'category': 'NN',
            'course': self.my_course.id}

    def test_create_weekly_recurrences_equiv(self):  # equivalence test
        """
        Equivalence Tests for creating weekly recurrences
        """
        self.data_form['end_recur_date'] = datetime.datetime(2020, 4, 6, 5, 0, 0,
                                                             tzinfo=pytz.utc)

        weekly_occurrence = create_from_data_dict(self.data_form)  # create first instance

        # should create 4 instances
        self.client.post(reverse('todo_list:create_recurrences', kwargs={'todo_item_id': weekly_occurrence.id}),
                         self.data_form)
        current_query_set = ToDoItem.objects.all()
        self.assertEqual(4, len(current_query_set))

        # check crucial fields
        filtered = ToDoItem.objects.filter(title="Test creating weekly recurrences equivalence",
                                         recur_freq='WEEKLY',
                                         end_recur_date=datetime.datetime(2020, 4, 6, 5, 0, 0, tzinfo=pytz.utc))
        self.assertEqual(4, len(filtered))

        # check duedates of all 4 objects
        count_true = 0
        for i in range(len(filtered) - 1):
            if filtered[i].duedate == filtered[i + 1].duedate - relativedelta(weeks=1):
                count_true += 1

        # count_true has to be 3 because 3 comparisons if test works
        self.assertEqual(3, count_true)

    ################## boundary tests ######################
    def test_create_less_than_a_full_week(self):
        """
        end_recur_date is not a full 4 weeks --> should create only 3 instances
        """
        self.data_form['title'] = "Test creating weekly recurrences boundaries"
        self.data_form['description'] = "end_recur_date is not a full 4 weeks"
        self.data_form['end_recur_date'] = datetime.datetime(2020, 4, 5, 5, 0, 0, tzinfo=pytz.utc)

        weekly_occurrence = create_from_data_dict(self.data_form)  # create first instance

        # should create 3 instances
        self.client.post(reverse('todo_list:create_recurrences', kwargs={'todo_item_id': weekly_occurrence.id}),
                         self.data_form)
        current_query_set = ToDoItem.objects.all()
        self.assertEqual(3, len(current_query_set))

        # check crucial fields
        filtered = ToDoItem.objects.filter(title="Test creating weekly recurrences boundaries",
                                            description="end_recur_date is not a full 4 weeks",
                                            recur_freq='WEEKLY',
                                            end_recur_date=datetime.datetime(2020, 4, 5, 5, 0, 0, tzinfo=pytz.utc)
                                         )
        self.assertEqual(3, len(filtered))

        # check duedates of all 3 objects
        count_true = 0
        for i in range(len(filtered) - 1):
            if filtered[i].duedate == filtered[i + 1].duedate - relativedelta(weeks=1):
                count_true += 1

        # count_true has to be 2 because 2 comparisons if test works
        self.assertEqual(2, count_true)

    def test_create_more_than_a_full_week(self):
        """
        end_recur_date is more than a full 4 weeks --> should create 4 instances
        """
        self.data_form['title'] = "Test creating weekly recurrences boundaries"
        self.data_form['description'] = "end_recur_date is more than 4 weeks but less than 5 weeks"
        self.data_form['end_recur_date'] = datetime.datetime(2020, 4, 8, 5, 0, 0, tzinfo=pytz.utc)

        weekly_occurrence = create_from_data_dict(self.data_form)  # create first instance

        # should create 3 instances
        self.client.post(reverse('todo_list:create_recurrences', kwargs={'todo_item_id': weekly_occurrence.id}),
                         self.data_form)
        current_query_set = ToDoItem.objects.all()
        self.assertEqual(4, len(current_query_set))

        # check crucial fields
        # check titles
        filtered = ToDoItem.objects.filter(title="Test creating weekly recurrences boundaries",
                                            description="end_recur_date is more than 4 weeks but less than 5 weeks",
                                            recur_freq='WEEKLY',
                                            end_recur_date=datetime.datetime(2020, 4, 8, 5, 0, 0, tzinfo=pytz.utc)
                                         )
        self.assertEqual(4, len(filtered))

        # check duedates of all 4 objects
        count_true = 0
        # check due date
        for i in range(len(filtered) - 1):
            if filtered[i].duedate == filtered[i + 1].duedate - relativedelta(weeks=1):
                count_true += 1

        # count_true has to be 3 because 3 comparisons if test works
        self.assertEqual(3, count_true)

    def test_create_full_week_but_less_time(self):
        """
        end_recur_date is not a full 4 weeks --> should create only 3 instances
        """
        self.data_form['title'] = "Test creating weekly recurrences boundaries"
        self.data_form['description'] = "end_recur_date is 4 weeks by day but not 4 weeks by time"
        self.data_form['end_recur_date'] = datetime.datetime(2020, 4, 5, 3, 0, 0, tzinfo=pytz.utc)

        weekly_occurrence = create_from_data_dict(self.data_form)  # create first instance

        # should create 3 instances
        self.client.post(reverse('todo_list:create_recurrences', kwargs={'todo_item_id': weekly_occurrence.id}),
                         self.data_form)
        current_query_set = ToDoItem.objects.all()
        self.assertEqual(3, len(current_query_set))

        # check crucial fields
        filtered = ToDoItem.objects.filter(title="Test creating weekly recurrences boundaries",
                                            description="end_recur_date is 4 weeks by day but not 4 weeks by time",
                                            recur_freq='WEEKLY',
                                            end_recur_date=datetime.datetime(2020, 4, 5, 3, 0, 0, tzinfo=pytz.utc)
                                         )
        self.assertEqual(3, len(filtered))

        # check duedates of all 3 objects
        count_true = 0
        for i in range(len(filtered) - 1):
            if filtered[i].duedate == filtered[i + 1].duedate - relativedelta(weeks=1):
                count_true += 1

        # count_true has to be 2 because 2 comparisons if test works
        self.assertEqual(2, count_true)

    def test_end_date_earlier_than_duedate_weekly(self):
        """
        Create end_recur_date earlier than duedate --> should create only one instance
        """
        self.data_form['title'] = "Test creating weekly recurrences"
        self.data_form['description'] = "Some end_recur_date earlier than duedate"
        self.data_form['end_recur_date'] = datetime.datetime(2020, 3, 10, 4, 0, 0, tzinfo=pytz.utc)

        weekly_occurrence = create_from_data_dict(self.data_form)  # create first instance
        # print( daily_occurrence.id )
        # should create 1 instance
        self.client.post(reverse('todo_list:create_recurrences', kwargs={'todo_item_id': weekly_occurrence.id}),
                         self.data_form)
        current_instance = ToDoItem.objects.get(description="Some end_recur_date earlier than duedate")
        all_instances = [current_instance]

        self.assertEqual(1, len(all_instances))

        # check crucial fields
        one_instance = ToDoItem.objects.get(title="Test creating weekly recurrences",
                                            description="Some end_recur_date earlier than duedate",
                                            end_recur_date=datetime.datetime(2020, 3, 10, 4, 0, 0, tzinfo=pytz.utc))

        # check duedates of  1 object
        self.assertEqual(one_instance.duedate, datetime.datetime(2020, 3, 16, 5, 0, 0, tzinfo=pytz.utc))

    def tearDown(self):
        del self.my_course
        del self.data_form


class CreateMonthlyRecurrencesTests(TestCase):
    def setUp(self):
        self.my_course = create_course(
            new_course_name="Tester"
        )

        # this data will be passed into the Forms and create/update object
        self.data_form = {
            'title': "Test creating monthly recurrences",
            'description': '',
            'duedate': datetime.datetime(2020, 3, 16, 5, 0, 0, tzinfo=pytz.utc),
            'location': '',
            'recur_freq': 'MONTHLY',
            'end_recur_date': datetime.datetime(2020, 6, 16, 5, 0, 0, tzinfo=pytz.utc),
            'priority': 'LO',
            'category': 'NN',
            'course': self.my_course.id}

    def test_create_monthly_recurrences_equiv(self):  # equivalence test
        """
        Equivalence Tests for creating 4 monthly recurrences
        """
        monthly_occurrence = create_from_data_dict(self.data_form)  # create first instance

        # should create 4 instances
        self.client.post(reverse('todo_list:create_recurrences', kwargs={'todo_item_id': monthly_occurrence.id}),
                         self.data_form)
        current_query_set = ToDoItem.objects.all()
        self.assertEqual(4, len(current_query_set))

        # check crucial fields
        filtered = ToDoItem.objects.filter(title="Test creating monthly recurrences",
                                         recur_freq='MONTHLY',
                                         end_recur_date=datetime.datetime(2020, 6, 16, 5, 0, 0, tzinfo=pytz.utc))
        self.assertEqual(4, len(filtered))

        # check duedates of all 4 objects
        count_true = 0
        for i in range(len(filtered) - 1):
            if filtered[i].duedate == filtered[i + 1].duedate - relativedelta(months=1):
                count_true += 1

        # count_true has to be 3 because 3 comparisons if test works
        self.assertEqual(3, count_true)

    ################## boundary tests ######################
    def test_create_less_than_a_full_month_date(self):
        """
        end_recur_date is not a full 4 months --> should create only 3 instances
        """
        self.data_form['title'] = "Test creating monthly recurrences boundaries"
        self.data_form['description'] = "end_recur_date is not a full 4 months by dates"
        self.data_form['end_recur_date'] = datetime.datetime(2020, 5, 16, 5, 0, 0, tzinfo=pytz.utc)

        weekly_occurrence = create_from_data_dict(self.data_form)  # create first instance

        # should create 3 instances
        self.client.post(reverse('todo_list:create_recurrences', kwargs={'todo_item_id': weekly_occurrence.id}),
                         self.data_form)
        current_query_set = ToDoItem.objects.all()
        self.assertEqual(3, len(current_query_set))

        # check crucial fields
        # check titles
        filtered = ToDoItem.objects.filter(title="Test creating monthly recurrences boundaries",
                                            description= "end_recur_date is not a full 4 months by dates",
                                            recur_freq='MONTHLY',
                                            end_recur_date= datetime.datetime(2020, 5, 16, 5, 0, 0, tzinfo=pytz.utc)
                                         )
        self.assertEqual(3, len(filtered))

        # check duedates of all 3 objects
        count_true = 0
        for i in range(len(filtered) - 1):
            if filtered[i].duedate == filtered[i + 1].duedate - relativedelta(months=1):
                count_true += 1

        # count_true has to be 2 because 2 comparisons if test works
        self.assertEqual(2, count_true)

    def test_create_less_than_a_full_month_time(self):
        """
        end_recur_date is not a full 4 months by time --> should create only 3 instances
        """
        self.data_form['title'] = "Test creating monthly recurrences boundaries"
        self.data_form['description'] = "end_recur_date is not a full 4 months by time"
        self.data_form['end_recur_date'] = datetime.datetime(2020, 5, 16, 4, 0, 0, tzinfo=pytz.utc)

        monthly_occurrence = create_from_data_dict(self.data_form)  # create first instance

        # should create 3 instances
        self.client.post(reverse('todo_list:create_recurrences', kwargs={'todo_item_id': monthly_occurrence.id}),
                         self.data_form)
        current_query_set = ToDoItem.objects.all()
        self.assertEqual(3, len(current_query_set))

        # check crucial fields
        filtered = ToDoItem.objects.filter(title="Test creating monthly recurrences boundaries",
                                            description= "end_recur_date is not a full 4 months by time",
                                            recur_freq='MONTHLY',
                                            end_recur_date= datetime.datetime(2020, 5, 16, 4, 0, 0, tzinfo=pytz.utc)
                                         )
        self.assertEqual(3, len(filtered))

        # check duedates of all 3 objects
        count_true = 0
        for i in range(len(filtered) - 1):
            if filtered[i].duedate == filtered[i + 1].duedate - relativedelta(months=1):
                count_true += 1

        # count_true has to be 3 because 3 comparisons if test works
        self.assertEqual(2, count_true)

    def test_create_more_than_a_full_month_dates(self):
        """
        end_recur_date is more than a full 4 month --> should create 4 instances
        """
        self.data_form['title'] = "Test creating monthly recurrences boundaries"
        self.data_form['description'] = "end_recur_date is more than 4 months but less than 5 months by dates"
        self.data_form['end_recur_date'] = datetime.datetime(2020, 6, 30, 5, 0, 0, tzinfo=pytz.utc)

        monthly_occurrence = create_from_data_dict(self.data_form)  # create first instance

        # should create 4 instances
        self.client.post(reverse('todo_list:create_recurrences', kwargs={'todo_item_id': monthly_occurrence.id}),
                         self.data_form)
        current_query_set = ToDoItem.objects.all()
        self.assertEqual(4, len(current_query_set))

        # check crucial fields
        # check titles
        filtered = ToDoItem.objects.filter(title= "Test creating monthly recurrences boundaries",
                                            description="end_recur_date is more than 4 months but less than 5 months by dates",
                                            recur_freq='MONTHLY',
                                            end_recur_date=datetime.datetime(2020, 6, 30, 5, 0, 0, tzinfo=pytz.utc)
                                         )
        self.assertEqual(4, len(filtered))

        # check duedates of all 4 objects
        count_true = 0
        # check due date
        for i in range(len(filtered) - 1):
            if filtered[i].duedate == filtered[i + 1].duedate - relativedelta(months=1):
                count_true += 1

        # count_true has to be 3 because 3 comparisons if test works
        self.assertEqual(3, count_true)

    def test_create_more_than_a_full_month_time(self):
        """
        end_recur_date is more than a full 4 months --> should create 4 instances
        """
        self.data_form['title'] = "Test creating monthly recurrences boundaries"
        self.data_form['description'] = "end_recur_date is more than 4 months but less than 5 months by time"
        self.data_form['end_recur_date'] = datetime.datetime(2020, 6, 16, 5, 1, 0, tzinfo=pytz.utc)

        monthly_occurrence = create_from_data_dict(self.data_form)  # create first instance

        # should create 4 instances
        self.client.post(reverse('todo_list:create_recurrences', kwargs={'todo_item_id': monthly_occurrence.id}),
                         self.data_form)
        current_query_set = ToDoItem.objects.all()
        self.assertEqual(4, len(current_query_set))

        # check crucial fields
        filtered = ToDoItem.objects.filter(title= "Test creating monthly recurrences boundaries",
                                            description="end_recur_date is more than 4 months but less than 5 months by time",
                                            recur_freq='MONTHLY',
                                            end_recur_date=datetime.datetime(2020, 6, 16, 5, 1, 0, tzinfo=pytz.utc)
                                         )
        self.assertEqual(4, len(filtered))

        # check duedates of all 4 objects
        count_true = 0
        for i in range(len(filtered) - 1):
            if filtered[i].duedate == filtered[i + 1].duedate - relativedelta(months=1):
                count_true += 1

        # count_true has to be 3 because 3 comparisons if test works
        self.assertEqual(3, count_true)

    def test_end_date_earlier_than_duedate_month(self): #edge case
        """
        Create end_recur_date earlier than duedate --> should create only one instance

        """
        self.data_form['title'] = "Test creating monthly recurrences"
        self.data_form['description'] = "Some end_recur_date earlier than duedate by month and time"
        self.data_form['end_recur_date'] = datetime.datetime(2020, 2, 10, 4, 0, 0, tzinfo=pytz.utc)

        yearly_occurrence = create_from_data_dict(self.data_form)  # create first instance

        # should create 1 instance
        self.client.post(reverse('todo_list:create_recurrences', kwargs={'todo_item_id': yearly_occurrence.id}),
                         self.data_form)
        current_instance = ToDoItem.objects.get(description="Some end_recur_date earlier than duedate by month and time")
        all_instances = [current_instance]

        self.assertEqual(1, len(all_instances))

        # check crucial fields

        one_instance = ToDoItem.objects.get(title="Test creating monthly recurrences",
                                            description="Some end_recur_date earlier than duedate by month and time",
                                            end_recur_date=datetime.datetime(2020, 2, 10, 4, 0, 0, tzinfo=pytz.utc))

        # check duedates of  1 object
        self.assertEqual(one_instance.duedate, datetime.datetime(2020, 3, 16, 5, 0, 0, tzinfo=pytz.utc))

class CreateYearlyRecurrencesTests(TestCase):
    def setUp(self):
        self.my_course = create_course(
            new_course_name="Tester"
        )

        # this data will be passed into the Forms and create/update object
        self.data_form = {
            'title': "Test creating yearly recurrences",
            'description': '',
            'duedate': datetime.datetime(2020, 3, 16, 5, 0, 0, tzinfo=pytz.utc),
            'location': '',
            'recur_freq': 'YEARLY',
            'end_recur_date': datetime.datetime(2023, 3, 16, 5, 0, 0, tzinfo=pytz.utc),
            'priority': 'LO',
            'category': 'NN',
            'course': self.my_course.id}

    def test_create_yearly_recurrences_equiv(self):  # equivalence test
        """
        Equivalence Tests for creating 4 yearly recurrences
        """
        yearly_occurrence = create_from_data_dict(self.data_form)  # create first instance

        # should create 4 instances
        self.client.post(reverse('todo_list:create_recurrences', kwargs={'todo_item_id': yearly_occurrence.id}),
                         self.data_form)
        current_query_set = ToDoItem.objects.all()
        self.assertEqual(4, len(current_query_set))

        # check crucial fields
        filtered = ToDoItem.objects.filter(title="Test creating yearly recurrences",
                                         recur_freq='YEARLY',
                                         end_recur_date=datetime.datetime(2023, 3, 16, 5, 0, 0, tzinfo=pytz.utc))
        self.assertEqual(4, len(filtered))

        # check duedates of all 4 objects
        count_true = 0
        for i in range(len(filtered) - 1):
            if filtered[i].duedate == filtered[i + 1].duedate - relativedelta(years=1):
                count_true += 1

        # count_true has to be 3 because 3 comparisons if test works
        self.assertEqual(3, count_true)

    ################## boundary tests ######################
    def test_create_less_than_a_full_year_dates(self):
        """
        end_recur_date is not a full 4 years --> should create only 3 instances
        """
        self.data_form['title'] = "Test creating yearly recurrences boundaries"
        self.data_form['description'] = "end_recur_date is not a full 4 years by dates"
        self.data_form['end_recur_date'] = datetime.datetime(2023, 2, 16, 5, 0, 0, tzinfo=pytz.utc)

        yearly_occurrence = create_from_data_dict(self.data_form)  # create first instance

        # should create 3 instances
        self.client.post(reverse('todo_list:create_recurrences', kwargs={'todo_item_id': yearly_occurrence.id}),
                         self.data_form)
        current_query_set = ToDoItem.objects.all()
        self.assertEqual(3, len(current_query_set))

        # check crucial fields
        # check titles
        filtered = ToDoItem.objects.filter(title="Test creating yearly recurrences boundaries",
                                            description= "end_recur_date is not a full 4 years by dates",
                                            recur_freq='YEARLY',
                                            end_recur_date= datetime.datetime(2023, 2, 16, 5, 0, 0, tzinfo=pytz.utc)
                                         )
        self.assertEqual(3, len(filtered))

        # check duedates of all 3 objects
        count_true = 0
        # check due date
        for i in range(len(filtered) - 1):
            if filtered[i].duedate == filtered[i + 1].duedate - relativedelta(years=1):
                count_true += 1

        # count_true has to be 2 because 2 comparisons if test works
        self.assertEqual(2, count_true)

    def test_create_less_than_a_full_year_time(self):
        """
        end_recur_date is not a full 4 years but only by time --> should create only 4 instances
        """
        self.data_form['title'] = "Test creating yearly recurrences boundaries"
        self.data_form['description'] = "end_recur_date is not a full 4 years by time"
        self.data_form['end_recur_date'] = datetime.datetime(2023, 3, 16, 4, 0, 0, tzinfo=pytz.utc)

        yearly_occurrence = create_from_data_dict(self.data_form)  # create first instance

        # should create 3 instances
        self.client.post(reverse('todo_list:create_recurrences', kwargs={'todo_item_id': yearly_occurrence.id}),
                         self.data_form)
        current_query_set = ToDoItem.objects.all()

        self.assertEqual(3, len(current_query_set))

        # check crucial fields
        # check titles
        filtered = ToDoItem.objects.filter(title="Test creating yearly recurrences boundaries",
                                            description= "end_recur_date is not a full 4 years by time",
                                            recur_freq='YEARLY',
                                            end_recur_date= datetime.datetime(2023, 3, 16, 4, 0, 0, tzinfo=pytz.utc)
                                         )
        self.assertEqual(3, len(filtered))

        # check duedates of all 3 objects
        count_true = 0
        # check due date
        for i in range(len(filtered) - 1):
            if filtered[i].duedate == filtered[i + 1].duedate - relativedelta(years=1):
                count_true += 1

        # count_true has to be 2 because 2 comparisons if test works
        self.assertEqual(2, count_true)

    def test_create_more_than_a_full_year_dates(self):
        """
        end_recur_date is more than a full 4 years --> should create 4 instances
        """
        self.data_form['title'] = "Test creating yearly recurrences boundaries"
        self.data_form['description'] = "end_recur_date is more than 4 years but less than 5 years by dates"
        self.data_form['end_recur_date'] = datetime.datetime(2023, 4, 30, 5, 0, 0, tzinfo=pytz.utc)

        yearly_occurrence = create_from_data_dict(self.data_form)  # create first instance

        # should create 4 instances
        self.client.post(reverse('todo_list:create_recurrences', kwargs={'todo_item_id': yearly_occurrence.id}),
                         self.data_form)
        current_query_set = ToDoItem.objects.all()

        self.assertEqual(4, len(current_query_set))

        # check crucial fields
        # check titles
        filtered = ToDoItem.objects.filter(title= "Test creating yearly recurrences boundaries",
                                            description= "end_recur_date is more than 4 years but less than 5 years by dates",
                                            recur_freq='YEARLY',
                                            end_recur_date=datetime.datetime(2023, 4, 30, 5, 0, 0, tzinfo=pytz.utc)
                                         )
        self.assertEqual(4, len(filtered))

        # check duedates of all 4 objects
        count_true = 0
        # check due date
        for i in range(len(filtered) - 1):
            if filtered[i].duedate == filtered[i + 1].duedate - relativedelta(years=1):
                count_true += 1

        # count_true has to be 3 because 3 comparisons if test works
        self.assertEqual(3, count_true)

    def test_create_more_than_a_full_year_time(self):
        """
        end_recur_date is not a full 4 years --> should create 4 instances
        """
        self.data_form['title'] = "Test creating yearly recurrences boundaries"
        self.data_form['description'] = "end_recur_date is more than 4 years but less than 5 years by time"
        self.data_form['end_recur_date'] = datetime.datetime(2023, 3, 16, 6, 0, 0, tzinfo=pytz.utc)

        yearly_occurrence = create_from_data_dict(self.data_form)  # create first instance

        # should create 4 instances
        self.client.post(reverse('todo_list:create_recurrences', kwargs={'todo_item_id': yearly_occurrence.id}),
                         self.data_form)
        current_query_set = ToDoItem.objects.all()
        self.assertEqual(4, len(current_query_set))

        # check crucial fields
        # check titles
        filtered = ToDoItem.objects.filter(title= "Test creating yearly recurrences boundaries",
                                            description="end_recur_date is more than 4 years but less than 5 years by time",
                                            recur_freq='YEARLY',
                                            end_recur_date=datetime.datetime(2023, 3, 16, 6, 0, 0, tzinfo=pytz.utc)
                                         )
        self.assertEqual(4, len(filtered))

        # check duedates of all 4 objects
        count_true = 0
        # check due date
        for i in range(len(filtered) - 1):
            if filtered[i].duedate == filtered[i + 1].duedate - relativedelta(years=1):
                count_true += 1

        # count_true has to be 3 because 3 comparisons if test works
        self.assertEqual(3, count_true)

    def test_end_date_earlier_than_duedate_year(self): #edge case
        """
        Create end_recur_date earlier than duedate --> should create only one instance
        """
        self.data_form['title'] = "Test creating yearly recurrences"
        self.data_form['description'] = "Some end_recur_date earlier than duedate by year"
        self.data_form['end_recur_date'] = datetime.datetime(2019, 2, 10, 4, 0, 0, tzinfo=pytz.utc)

        yearly_occurrence = create_from_data_dict(self.data_form)  # create first instance

        self.client.post(reverse('todo_list:create_recurrences', kwargs={'todo_item_id': yearly_occurrence.id}),
                         self.data_form)
        current_instance = ToDoItem.objects.get(description="Some end_recur_date earlier than duedate by year")
        all_instances = [current_instance]

        self.assertEqual(1, len(all_instances))

        # check crucial fields
        one_instance = ToDoItem.objects.get(title="Test creating yearly recurrences",
                                            description="Some end_recur_date earlier than duedate by year",
                                            recur_freq = 'YEARLY',
                                            end_recur_date=datetime.datetime(2019, 2, 10, 4, 0, 0, tzinfo=pytz.utc))

        # check duedates of  1 object
        self.assertEqual(one_instance.duedate, datetime.datetime(2020, 3, 16, 5, 0, 0, tzinfo=pytz.utc))

class UpdateViewTest(TestCase):
    def setUp(self):
        self.my_course = create_course(
            new_course_name="Tester"
        )

        self.data_form_daily = {
            'title': "Change title test",
            'description': '',
            'duedate': datetime.datetime(2020, 3, 16, 5, 0, 0, tzinfo=pytz.utc),
            'location': '',
            'recur_freq': 'DAILY',
            'end_recur_date': datetime.datetime(2020, 3, 19, 5, 0, 0, tzinfo=pytz.utc),
            'priority': 'LO',
            'category': 'NN',
            'course': self.my_course.id}
        self.daily_occurrence = create_from_data_dict(self.data_form_daily)

    def test_correct_template_for_updateview(self):
        response = self.client.post(
            reverse('todo_list:detail', kwargs={'pk': self.daily_occurrence.id}),
            self.data_form_daily)
        self.assertTemplateUsed(response, 'todo/edit_todoitem_form.html')

    def test_edit_todoitemform_success_submission(self):
        self.data_form_daily['title'] = 'Change submit'
        form = ToDoForm(data=self.data_form_daily)
        self.assertTrue(form.is_valid())

    # def test_change_only_one_todo_title(self):
    #
    #     #print( self.daily_occurrence.id)
    #     self.assertEqual( 21, self.daily_occurrence.id )
    #     print( ToDoItem.objects.all())
    #     self.data_form_daily['title'] = "Change title test success"
    #     self.data_form_daily['change-once'] = 'Submit'
    #
    #     # self.daily_occurrence = create_from_data_dict(self.data_form_daily)
    #     # print(ToDoItem.objects.all())
    #
    #     response = self.client.post(
    #         reverse('todo_list:detail', kwargs={'pk': self.daily_occurrence.id}),
    #         self.data_form_daily,
    #     )
    #
    #     self.daily_occurrence.refresh_from_db()
    #     #self.assertRedirects(response, reverse('todo_list:change_all', kwargs={'todo_item_id':self.daily_occurrence.id}))
    #     #self.assertEqual(self.daily_occurrence.title, "Change title test success")

    def tearDown(self):
        del self.my_course
        del self.data_form_daily
        del self.daily_occurrence