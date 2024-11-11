from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django import forms
from .models import CustomUser, Enrollment
from .models import Booking
from .models import LessonBooking
from .models import Enrollment, CustomUser
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from .models import CustomUser, Enrollment, Course, Lesson, LessonBooking
from .models import Lesson




class RegisterForm(UserCreationForm):
    full_name = forms.CharField(max_length=255)
    phone_number = forms.CharField(max_length=15)
    gender = forms.ChoiceField(choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    interests = forms.CharField(widget=forms.Textarea)
    hobbies = forms.CharField(widget=forms.Textarea)
    countries_travelled = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = CustomUser
        fields = [
            'username', 'full_name', 'email', 'phone_number', 'gender', 
            'level', 'interests', 'hobbies', 'countries_travelled', 
            'password1', 'password2'
        ]


class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(label="Username or Email")
    password = forms.CharField(widget=forms.PasswordInput)

class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, required=True)  # Add the role field here

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'role') 



class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['enrollment_type']



class LessonBookingForm(forms.ModelForm):
    class Meta:
        model = LessonBooking
        fields = ['user', 'lesson', 'lesson_type', 'schedule']


class CustomUserCreationForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'role', 'level']
        widgets = {
            'password': forms.PasswordInput(),
        }

class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['user', 'course', 'enrollment_type']


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'course_type', 'lessons_count', 'price_in_yen', 'image', 'materials']

class EditUserRoleForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['role'] 

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = [
            'title', 'course', 'content', 'video_url', 'start_time', 
            'duration', 'zoom_link', 'materials', 'completed', 'teacher'
        ]