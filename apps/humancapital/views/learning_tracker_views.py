
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone


@login_required
def learning_dashboard(request):
    today = timezone.localdate()

    try:
        selected_year = int(request.GET.get("year", today.year))
    except (ValueError, TypeError):
        selected_year = today.year

    year_options = range(today.year - 2, today.year + 3)

    # Dummy registration trend (January - December)
    month_labels = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ]

    month_values = [
        12, 18, 15, 24, 32, 28,
        35, 42, 38, 45, 30, 20
    ]

    # Dummy recent approvals
    recent_approvals = [
        {
            "employee": "Andi Pratama",
            "cat": today - timedelta(days=1),
            "schedule": None,
            "external_topic_title": "Leadership Development",
            "code": "ENR-001",
            "approval_status": "approved",
        },
        {
            "employee": "Siti Rahmawati",
            "cat": today - timedelta(days=2),
            "schedule": None,
            "external_topic_title": "Effective Communication",
            "code": "ENR-002",
            "approval_status": "pending",
        },
        {
            "employee": "Budi Santoso",
            "cat": today - timedelta(days=3),
            "schedule": None,
            "external_topic_title": "Data Analysis Fundamentals",
            "code": "ENR-003",
            "approval_status": "rejected",
        },
    ]

    # Dummy upcoming schedules
    upcoming_schedules = [
        {
            "topic": {"name": "Effective Communication"},
            "start_time": timezone.now() + timedelta(days=2),
            "end_time": timezone.now() + timedelta(days=2, hours=2),
            "location_or_link": "Meeting Room A",
            "training_type": "offline",
        },
        {
            "topic": {"name": "Leadership Development"},
            "start_time": timezone.now() + timedelta(days=4),
            "end_time": timezone.now() + timedelta(days=4, hours=2),
            "location_or_link": "Microsoft Teams",
            "training_type": "online",
        },
    ]

    context = {
        "selected_year": selected_year,
        "year_options": year_options,
        "total_training": 24,
        "total_participants": 156,
        "new_registrations": 18,
        "ongoing_training": 5,
        "total_registrations": sum(month_values),
        "month_labels": month_labels,
        "month_values": month_values,
        "approved": 120,
        "pending": 25,
        "rejected": 11,
        "other": 0,
        "recent_approvals": recent_approvals,
        "upcoming_schedules": upcoming_schedules,
    }

    return render(
        request,
        "learning_tracker/dashboard.html",
        context,
    )

@login_required
def learning_user_dashboard(request):
    # Dummy data: replace with ORM queries when the database integration is ready.
    context = {
        "display_name": request.user.first_name or request.user.username.title(),
        "training_complete": 18,
        "learning_hours": 42.5,
        "average_score": 88.4,
        "not_completed": 3,
        "training_growth": 28.6,
        "training_scores": [
            {
                "name": "Communication",
                "score": 95,
                "color": "#e96367",
            },
            {
                "name": "Leadership",
                "score": 85,
                "color": "#91a8ee",
            },
            {
                "name": "Data Analysis",
                "score": 78,
                "color": "#d5d5d5",
            },
            {
                "name": "Time Management",
                "score": 90,
                "color": "#e96367",
            },
        ],
        "grade_summary": [
            {"label": "Completed", "range": "90–100", "count": 7, "color": "#ff5379"},
            {"label": "Remedial", "range": "80–89", "count": 7, "color": "#ffbd4a"},
            {"label": "Not Completed", "range": "0–79", "count": 3, "color": "#bfbfbf"},
        ],
        "public_trainings": [
            {"title": "Lead with Impact: Essential Skills for New Managers", "date": "18 October 2026", "time": "09.00 - 12.00", "trainer": "Azriel Hardi", "seats": 12, "category": "Classroom", "image_url": ""},
            {"title": "Data Analysis Fundamentals for Business", "date": "24 October 2026", "time": "13.00 - 16.00", "trainer": "Diana Putri", "seats": 25, "category": "Online", "image_url": ""},
            {"title": "Effective Communication in the Workplace", "date": "30 October 2026", "time": "10.00 - 12.00", "trainer": "Rizky Maulana", "seats": 50, "category": "Webinar", "image_url": ""},
            {"title": "Effective Communication in the Workplace", "date": "30 October 2026", "time": "10.00 - 12.00", "trainer": "Rizky Maulana", "seats": 50, "category": "Webinar", "image_url": ""},
            {"title": "Effective Communication in the Workplace", "date": "30 October 2026", "time": "10.00 - 12.00", "trainer": "Rizky Maulana", "seats": 50, "category": "Webinar", "image_url": ""},
        ],
    }
    return render(request, "learning_tracker/user_dashboard.html", context)

