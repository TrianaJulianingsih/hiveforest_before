# Tambahkan fungsi ini ke file View Learning Tracker yang sudah ada.
# Pastikan import login_required dan render tersedia.
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def learning_my_training(request):
    # DUMMY DATA: nanti diganti dengan query ke model Employee,
    # HumancapitalLearningEnrollment, dan HumancapitalLearningCompletion.
    scheduled_trainings = [
        {
            "topic": "Change Management for CIBG Sales",
            "schedule": "10 August 2026 | 08.30 - 11.00",
            "trainer": "CIBG",
            "invitation_status": "Invited",
            "program_url": "",  # Isi dengan URL yang valid setelah tersedia.
            "training_status": "Completed",
            "status_color": "green",
            "pre_test": 100,
            "post_test": 100,
        }
        for _ in range(3)
    ]

    ecourses = [
        {
            "topic": "Change Management for CIBG Sales",
            "url": "",  # Isi URL e-course yang valid setelah tersedia.
            "training_status": status,
            "status_color": color,
            "pre_test": 100,
            "post_test": 100,
        }
        for status, color in [
            ("Completed", "green"),
            ("Not Completed", "gray"),
            ("Progress", "blue"),
        ]
    ]

    context = {
        "employee_name": "Triana Julianingsih",
        "employee_initial": "T",
        "employee_nip": "0428",
        "employee_position": "INTERN IT",
        "employee_location": "JAKARTA",
        "otsukapedia_url": "",  # Belum ada URL asli.
        "total_training": 1,
        "total_ecourse": 1,
        "remedial_count": 0,
        "completed_count": 1,
        "scheduled_trainings": scheduled_trainings,
        "ecourses": ecourses,
    }
    return render(request, "learning_tracker/my_training.html", context)
