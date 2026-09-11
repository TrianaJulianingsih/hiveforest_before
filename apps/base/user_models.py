from django.db import models
from django.contrib.auth.models import User


# ═══════════════════════════════════════════════════════════
# FaisalS | Forgot Password function, Periodic Password Change function, Forced Password Change function
# ═══════════════════════════════════════════════════════════


class ForcePasswordStatus(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    must_change_password = models.BooleanField(default=False)
    last_reset_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Force Password Status"
        verbose_name_plural = "Force Password Statuses"

    def __str__(self):
        return f"{self.user.username} - Must change: {self.must_change_password}"
