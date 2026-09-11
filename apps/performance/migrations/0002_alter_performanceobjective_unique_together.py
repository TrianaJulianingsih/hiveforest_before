from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("performance", "0001_initial"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="performanceobjective",
            unique_together={("performance_model", "code")},
        ),
    ]
