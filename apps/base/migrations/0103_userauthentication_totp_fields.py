from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0102_authentication_management"),
    ]

    operations = [
        migrations.AddField(
            model_name="userauthentication",
            name="authenticator_confirmed",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="userauthentication",
            name="authenticator_last_verified_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="userauthentication",
            name="authenticator_secret",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
    ]
