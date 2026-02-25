from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.db.models.signals import post_migrate
from django.dispatch import receiver


ROLE_GROUP_MAP = {
    'SUPER_ADMIN': 'Super Admin',
    'HR_MANAGER': 'HR Manager',
    'SUPERVISOR': 'Supervisor',
    'STAFF': 'Staff',
}


@receiver(post_migrate)
def create_default_groups(sender, **kwargs):
    for group_name in ROLE_GROUP_MAP.values():
        Group.objects.get_or_create(name=group_name)


@receiver(post_migrate)
def assign_default_superuser_group(sender, **kwargs):
    User = get_user_model()
    admins = User.objects.filter(is_superuser=True)
    group, _ = Group.objects.get_or_create(name='Super Admin')
    for admin in admins:
        admin.groups.add(group)


@receiver(post_save, sender=get_user_model())
def sync_user_group(sender, instance, **kwargs):
    group_name = ROLE_GROUP_MAP.get(instance.role)
    if not group_name:
        return
    group, _ = Group.objects.get_or_create(name=group_name)
    instance.groups.clear()
    instance.groups.add(group)
