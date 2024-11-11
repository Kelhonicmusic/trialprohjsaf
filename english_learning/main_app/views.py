from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.http import HttpResponse, HttpResponseForbidden
from django.utils import timezone
from django.conf import settings
from paypalrestsdk import Payment
from django.urls import reverse
from .forms import EditUserRoleForm
from .forms import LessonForm


import paypalrestsdk

from .models import Course, Enrollment, Lesson, Booking, LessonBooking
from .forms import RegisterForm, CustomLoginForm, EnrollmentForm

from .forms import CustomUserCreationForm, EnrollmentForm, CourseForm, LessonBookingForm
from django.contrib.auth.decorators import user_passes_test
from .models import CustomUser


# Home page showing all available courses
def home(request):
    courses = Course.objects.all()
    return render(request, 'main_app/home.html', {'courses': courses})


# Courses page (list all courses)
def courses(request):
    level_filter = request.GET.get('level', '')
    if level_filter:
        courses = Course.objects.filter(course_type=level_filter)
    else:
        courses = Course.objects.all()

    return render(request, 'main_app/courses.html', {'courses': courses})



# About page
def about(request):
    return render(request, 'main_app/about.html')


# Contact page
def contact(request):
    return render(request, 'main_app/contact.html')


# Register a new user
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Logs the user in immediately after registration
            return redirect('home')  # Redirect to home after successful registration
        else:
            print("Form errors:", form.errors)
    else:
        form = RegisterForm()
    return render(request, 'main_app/register.html', {'form': form})


# Custom login view
def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)  # Log the user in after authentication

            # Redirect based on user role
            if user.role == 'student':
                return redirect('student_dashboard')
            elif user.role == 'teacher':
                return redirect('teacher_dashboard')
            elif user.role == 'admin':
                return redirect('admin_dashboard')
            else:
                return redirect('home')  # Default fallback

    else:
        form = CustomLoginForm()

    return render(request, 'main_app/login.html', {'form': form})


# Dashboard for students
def student_dashboard(request):
    if request.user.role == 'student':
        # Get all enrollments for the current student
        enrollments = Enrollment.objects.filter(user=request.user)
        
        # Get the related courses from the enrollments
        enrolled_courses = [enrollment.course for enrollment in enrollments]
        
        # Get the lessons related to those courses
        lessons = []
        for course in enrolled_courses:
            lessons.extend(course.lessons.all())

        # Get the booked lessons for the student
        booked_lessons = LessonBooking.objects.filter(user=request.user)

        return render(request, 'main_app/student_dashboard.html', {
            'user': request.user,
            'enrolled_courses': enrolled_courses,
            'lessons': lessons,
            'booked_lessons': booked_lessons
        })
    else:
        return redirect('home')


def teacher_dashboard(request):
    # Fetch lessons assigned to the logged-in teacher
    lessons = Lesson.objects.filter(teacher=request.user)

    # Handle the POST request when a lesson is marked as completed
    if request.method == 'POST':
        # Get the lesson_id from the form submission
        lesson_id = request.POST.get('lesson_id')

        # Fetch the lesson object based on the ID
        lesson = Lesson.objects.get(id=lesson_id)

        # Mark the lesson as completed
        lesson.completed = True
        lesson.save()

        # Redirect to the teacher's dashboard after saving the changes
        return redirect('teacher_dashboard')

    # Render the dashboard with the list of lessons
    return render(request, 'main_app/teacher_dashboard.html', {'lessons': lessons})



# View details of a specific course
def course_detail(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    return render(request, 'main_app/course_detail.html', {'course': course})


# Enroll a student in a course
@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    user = request.user

    if Enrollment.objects.filter(user=user, course=course).exists():
        return HttpResponseForbidden("You are already enrolled in this course.")

    if request.method == 'POST':
        form = EnrollmentForm(request.POST)
        if form.is_valid():
            enrollment_type = form.cleaned_data['enrollment_type']

            # Save the enrollment for the user and course
            enrollment = form.save(commit=False)
            enrollment.user = user
            enrollment.course = course
            enrollment.save()

            # If paid enrollment, redirect to payment page
            if enrollment_type == 'paid':
                # Correct the redirection here
                return redirect('payment', enrollment_id=enrollment.id)
            else:
                # If free trial, show success message
                return render(request, 'main_app/enroll_course.html', {
                    'course': course,
                    'enrollment_success': True,
                })
        else:
            return render(request, 'main_app/enroll_course.html', {
                'course': course,
                'form': form,
                'error': "Please fix the errors in the form.",
            })
    else:
        form = EnrollmentForm(initial={'enrollment_type': 'free_trial'})

    return render(request, 'main_app/enroll_course.html', {'course': course, 'form': form})

# Payment view
def payment(request, enrollment_id):
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)
    # Handle payment process...
    return render(request, 'main_app/payment.html', {'enrollment': enrollment})


# Lessons page for a specific course
@login_required
def course_lessons(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    # Get the lessons related to the course
    lessons = course.lesson_set.all()

    return render(request, 'main_app/course_lessons.html', {'course': course, 'lessons': lessons})


# View details of a specific lesson
@login_required
def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    return render(request, 'main_app/lesson_detail.html', {'lesson': lesson})


# Book a lesson
@login_required
def book_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)

    if request.method == 'POST':
        lesson_type = request.POST.get('lesson_type')  # private, semi_private, group
        schedule = request.POST.get('schedule')  # The schedule selected by the student
        
        # Ensure the selected lesson type is valid
        if lesson_type not in ['private', 'semi_private', 'group']:
            return HttpResponse("Invalid lesson type.", status=400)
        
        # Parse the schedule input (assuming it's in the format YYYY-MM-DDTHH:MM)
        try:
            schedule = timezone.datetime.fromisoformat(schedule)
        except ValueError:
            return HttpResponse("Invalid schedule format.", status=400)

        # Check if the user has already booked this lesson
        if LessonBooking.objects.filter(user=request.user, lesson=lesson, lesson_type=lesson_type).exists():
            return HttpResponse("You have already booked this lesson.", status=400)

        # Create the booking
        LessonBooking.objects.create(
            user=request.user,
            lesson=lesson,
            course=lesson.course,
            lesson_type=lesson_type,
            schedule=schedule,
            status='booked',
        )

        return redirect('student_dashboard')  # Redirect to dashboard after booking

    return render(request, 'main_app/book_lesson.html', {'lesson': lesson})


# Initialize PayPal SDK
paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET
})

def payment_process(request, enrollment_id):
    # Retrieve the enrollment using the provided enrollment_id
    enrollment = Enrollment.objects.get(id=enrollment_id)

    if request.method == 'POST':
        # Process the payment information here
        # For example, updating the enrollment status to 'paid' or processing other details
        enrollment.status = 'paid'
        enrollment.save()

        # Return a success response
        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'failure'})

# Payment success handler
def payment_success(request):
    # Retrieve the payment and confirm
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')
    payment = Payment.find(payment_id)

    if payment.execute({"payer_id": payer_id}):
        # Enrollment was successful
        # Update enrollment status or add further logic if necessary
        enrollment = Enrollment.objects.get(id=payment.transactions[0].item_list.items[0].course.id)
        enrollment.status = 'paid'
        enrollment.save()

        # Redirect the user to the course lessons page or success page
        return redirect('course_lessons', course_id=payment.transactions[0].item_list.items[0].course.id)
    else:
        return HttpResponseForbidden("Payment could not be processed.")


# Payment cancel handler
def payment_cancel(request):
    return render(request, 'main_app/payment_cancel.html', {
        'message': 'Your payment was canceled. Please try again or contact support.'
    })



# Admin check to ensure only admin can access this page
def is_admin(user):
    return user.is_superuser

@user_passes_test(is_admin)
def admin_dashboard(request):
    users = CustomUser.objects.all()
    enrollments = Enrollment.objects.all()
    courses = Course.objects.all()
    bookings = LessonBooking.objects.all()
    return render(request, 'main_app/admin_dashboard.html', {
        'users': users,
        'enrollments': enrollments,
        'courses': courses,
        'bookings': bookings,
    })

# User Management Views
@user_passes_test(is_admin)
def add_user(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'main_app/add_user.html', {'form': form})

@user_passes_test(is_admin)
def edit_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)  # Retrieve the user by ID
    if request.method == 'POST':
        form = EditUserRoleForm(request.POST, instance=user)  # Populate form with existing user data
        if form.is_valid():
            form.save()  # Save the updated role
            return redirect('admin_dashboard')  # Redirect after saving
    else:
        form = EditUserRoleForm(instance=user)  # Prepopulate the form with the existing user's role

    return render(request, 'main_app/edit_user.html', {'form': form})

@user_passes_test(is_admin)
def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        user.delete()
        return redirect('admin_dashboard')
    return render(request, 'main_app/delete_user.html', {'user': user})

# Enrollment Management Views
@user_passes_test(is_admin)
def add_enrollment(request):
    if request.method == 'POST':
        form = EnrollmentForm(request.POST)
        if form.is_valid():
            form.save()  # Saves the enrollment
            return redirect('admin_dashboard')
    else:
        form = EnrollmentForm()

    return render(request, 'main_app/add_enrollment.html', {'form': form})

@user_passes_test(is_admin)
def edit_enrollment(request, enrollment_id):
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)
    if request.method == 'POST':
        form = EnrollmentForm(request.POST, instance=enrollment)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        form = EnrollmentForm(instance=enrollment)
    return render(request, 'main_app/edit_enrollment.html', {'form': form})

@user_passes_test(is_admin)
def delete_enrollment(request, enrollment_id):
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)
    if request.method == 'POST':
        enrollment.delete()
        return redirect('admin_dashboard')
    return render(request, 'main_app/delete_enrollment.html', {'enrollment': enrollment})

# Course Management Views
@user_passes_test(is_admin)
def add_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        form = CourseForm()
    return render(request, 'main_app/add_course.html', {'form': form})

@user_passes_test(is_admin)
def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        form = CourseForm(instance=course)
    return render(request, 'main_app/edit_course.html', {'form': form})

@user_passes_test(is_admin)
def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        course.delete()
        return redirect('admin_dashboard')
    return render(request, 'main_app/delete_course.html', {'course': course})

# LessonBooking Management Views
@user_passes_test(is_admin)
def add_booking(request):
    if request.method == 'POST':
        form = LessonBookingForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')  # Redirect to admin dashboard after successful booking
    else:
        form = LessonBookingForm()  # Initialize empty form for GET request

    return render(request, 'main_app/add_booking.html', {'form': form})

@user_passes_test(is_admin)
def edit_booking(request, booking_id):
    booking = get_object_or_404(LessonBooking, id=booking_id)
    if request.method == 'POST':
        form = LessonBookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        form = LessonBookingForm(instance=booking)
    return render(request, 'main_app/edit_booking.html', {'form': form})

@user_passes_test(is_admin)
def delete_booking(request, booking_id):
    booking = get_object_or_404(LessonBooking, id=booking_id)
    if request.method == 'POST':
        booking.delete()
        return redirect('admin_dashboard')
    return render(request, 'main_app/delete_booking.html', {'booking': booking})

@user_passes_test(lambda u: u.is_staff)  # You can also use 'u.is_superuser'
def add_lesson(request):
    if request.method == 'POST':
        form = LessonForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')  # Redirect to admin dashboard after lesson creation
    else:
        form = LessonForm()  # Initialize an empty form for GET request
    return render(request, 'main_app/add_lesson.html', {'form': form})

