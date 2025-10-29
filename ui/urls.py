from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LoginView
from .forms import BootstrapAuthForm

urlpatterns = [
    path('', views.index, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path("courses/", views.course_list, name="courses"),
    path("courses/<slug:slug>/", views.course_detail, name="course_detail"),
    path("courses/<slug:slug>/enroll/", views.course_enroll, name="course_enroll"),
    path("courses/<slug:slug>/learn/", views.course_learn, name="course_learn"),  # YANGI

    path('team/', views.team, name='team'),
    path('testimonial/', views.testimonial, name='testimonial'),
    path('library/', views.library, name='library'),


    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="ui/login.html",
            authentication_form=BootstrapAuthForm
        ),
        name="login"
    ),
    path("logout/", auth_views.LogoutView.as_view(next_page="home"), name="logout"),

        # Parolni tiklash oqimi (ixtiyoriy, lekin tavsiya)
    path("password-reset/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),

    path('register/', views.register, name='register'),

    path("torrens/", views.torrens_list, name="torrens_list"),
    path("torrens/new/", views.torrens_create, name="torrens_create"),
    path("torrens/<slug:slug>/", views.torrens_detail, name="torrens_detail"),
    path("torrens/<slug:slug>/take/", views.torrens_take, name="torrens_take"),
    path("torrens/<slug:slug>/grade/<int:submission_id>/", views.torrens_grade, name="torrens_grade"),
]
