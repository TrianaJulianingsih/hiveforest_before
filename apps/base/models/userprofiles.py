from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.base.models.abstracts import GenericAbstract
from apps.base.models.people import Gender, Person

# ╔════════════════════════════════════════════════════════════╗
# ║  Name: UserProfile                                         ║
# ║  Type: Model                                               ║
# ║  Purpose: Manage User Profile                              ║
# ╟────────────────────────────────────────────────────────────╢
# ║  Path: apps\base\models\userprofiles.                      ║
# ║  Created: ? by Setiadji                                    ║
# ║  Updates: Jul/14-2025 by Setiadji                          ║
# ╚════════════════════════════════════════════════════════════╝  
class UserProfile(GenericAbstract):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    person = models.OneToOneField(Person, on_delete=models.SET_NULL, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True, default='profile_pictures/default-user.png')
    bio = models.TextField(blank=True, null=True, verbose_name="Bio")
    language = models.CharField(max_length=10, choices=[('en', 'English'), ('id', 'Indonesian')], default='en', verbose_name="Language")
    timezone = models.CharField(max_length=50, default='Asia/Jakarta', verbose_name="Timezone")
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        permissions = [
            ("soft_delete", "Can delete items"),
            ("soft_restore", "Can restore deleted items"),
        ]
    
    def save(self, *args, **kwargs):
        if self.person and self.person.name:
            self.name = self.person.name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name or (self.person.full_name if self.person else "Unnamed Profile")

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        instance.userprofile.save()