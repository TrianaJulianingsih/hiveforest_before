from django.db import models

class NonDeletedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(dat__isnull=True)