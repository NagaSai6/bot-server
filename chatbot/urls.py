from django.urls import path 
from . import views

#URLCOnf

urlpatterns = [
    path('hello/',views.say_hello),
    path('scrap-the-website/',views.form_submission_api)
]