# Tambahkan import ini ke file View Learning Tracker yang sudah ada.
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def learning_training_schedule(request):
    # Dummy data untuk tampilan. Nanti bisa diganti query dari HumancapitalLearningSchedule.
    training_agendas = [
        {"date": "2026-10-18", "type": "Tatap Muka", "title": "Lead with Impact", "time": "09.00 - 12.00", "location": "Meeting Room Sakura"},
        {"date": "2026-10-18", "type": "Online", "title": "Lead with Impact", "time": "09.00 - 12.00", "location": "Microsoft Teams"},
        {"date": "2026-10-24", "type": "Tatap Muka", "title": "Effective Communication", "time": "13.00 - 15.00", "location": "Meeting Room Sakura"},
        {"date": "2026-11-05", "type": "Online", "title": "Data Analysis Fundamentals", "time": "09.00 - 11.00", "location": "Microsoft Teams"},
    ]
    return render(request, "learning_tracker/training_schedule.html", {
        "training_agendas": training_agendas,
        "calendar_year": 2026,
        "calendar_month": 10,
    })
