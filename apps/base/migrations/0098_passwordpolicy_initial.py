# Bridge migration to preserve numbering after PasswordPolicy was already created

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0094_merge_20260205_0944'),
    ]

    operations = []
