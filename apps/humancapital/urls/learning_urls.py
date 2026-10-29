from django.urls import path
from apps.humancapital.views.learning_tracker_views import learning_dashboard, learning_user_dashboard
from apps.humancapital.views.my_training_view import learning_my_training
from apps.humancapital.views.training_schedule_view import learning_training_schedule

urlpatterns = [
    path('dashboard/', learning_dashboard, name='learning_dashboard'),
    path("user/dashboard/", learning_user_dashboard, name="learning_user_dashboard",),
    path("user/my-training/", learning_my_training, name="learning_my_training",),
    path("user/training-schedule/", learning_training_schedule, name="learning_training_schedule",),
]
