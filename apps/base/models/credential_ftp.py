from django.db import models
from apps.base.models.abstracts import GenericAbstract

class CredentialFTP(GenericAbstract):

    username = models.CharField(max_length=5, blank=True, null=True, verbose_name='Username')
    password = models.CharField(max_length=20, blank=True, null=True, verbose_name='Password')
    url = models.CharField(max_length=100, blank=True, null=True, verbose_name='URL FTP')
    periode = models.CharField(max_length=8, blank=True, null=True, verbose_name='Periode Password')

    class Meta:
        verbose_name = "Credentials FTP"
        verbose_name_plural = "Cred FTP"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]