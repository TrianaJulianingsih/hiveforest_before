from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


# ═══════════════════════════════════════════════════════════
# Password History Model for tracking password changes
# ═══════════════════════════════════════════════════════════
class PasswordHistory(models.Model):
    """
    Stores the history of password changes for users.
    Used for validating that users don't reuse old passwords.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_history',
        verbose_name=_("User")
    )
    password_hash = models.CharField(
        max_length=255,
        verbose_name=_("Password Hash"),
        help_text=_("Hashed password for security")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("Date and time when password was changed")
    )
    changed_by = models.CharField(
        max_length=50,
        default="user",
        verbose_name=_("Changed By"),
        help_text=_("Who changed the password (e.g., 'user', 'admin', 'force_change')")
    )

    class Meta:
        verbose_name = _("Password History")
        verbose_name_plural = _("Password Histories")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

    def check_password(self, raw_password):
        """
        Check if the given raw password matches this history entry.
        
        Args:
            raw_password: The plain text password to check
            
        Returns:
            True if password matches, False otherwise
        """
        return check_password(raw_password, self.password_hash)

    @classmethod
    def create_entry(cls, user, raw_password, changed_by="user"):
        """
        Create a new password history entry for a user.
        
        Args:
            user: The User object
            raw_password: The plain text password to hash and store
            changed_by: String indicating who initiated the change
            
        Returns:
            The created PasswordHistory instance
        """
        password_hash = make_password(raw_password)
        return cls.objects.create(
            user=user,
            password_hash=password_hash,
            changed_by=changed_by
        )

    @classmethod
    def cleanup_old_entries(cls, user, keep_count=0):
        """
        Remove old password history entries, keeping only the most recent ones.
        
        Args:
            user: The User object
            keep_count: Number of recent entries to keep (0 = keep all)
        """
        if keep_count <= 0:
            return
        
        # Get all entries for the user, ordered by date
        all_entries = cls.objects.filter(user=user).order_by("-created_at")
        
        # Keep only the most recent keep_count entries
        entries_to_delete = all_entries[keep_count:]
        for entry in entries_to_delete:
            entry.delete()

    @classmethod
    def get_user_password_history(cls, user, limit=None):
        """
        Get password history for a user.
        
        Args:
            user: The User object
            limit: Maximum number of entries to return (None = all)
            
        Returns:
            QuerySet of PasswordHistory objects
        """
        qs = cls.objects.filter(user=user).order_by("-created_at")
        if limit:
            qs = qs[:limit]
        return qs
