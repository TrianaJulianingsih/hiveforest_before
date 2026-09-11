from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.cms.models.appmanagers import ApplicationList
from apps.cms.models.modmanagers import ModuleList

@receiver(post_save, sender=ApplicationList)
def update_modulelist_code_on_application_save(sender, instance, created, **kwargs):
    if not created:  # Only update if the ApplicationList is not newly created
        for module_list in ModuleList.objects.filter(application=instance):
            module_list.code = f"{instance.code}-{module_list.initial}"
            module_list.save()

@receiver(post_delete, sender=ApplicationList)
def delete_related_modulelist_on_application_delete(sender, instance, **kwargs):
    ModuleList.objects.filter(application=instance).delete()

# @receiver(post_save, sender=ModuleList) 
# def update_modulelist_code_on_module_save(sender, instance, created, **kwargs):
#     if created: 
#         instance.code = f"{instance.application.code}-{instance.initial}"
#         instance.save()

@receiver(post_save, sender=ModuleList)
def update_modulelist_code_on_module_save(sender, instance, created, **kwargs):
    if created:
        ModuleList.objects.filter(pk=instance.pk).update(
            code=f"{instance.application.code}-{instance.initial}"
        )