from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def copy_document_owner_to_user(apps, schema_editor):
    EmployeeDocument = apps.get_model('employees', 'EmployeeDocument')
    for document in EmployeeDocument.objects.select_related('employee_profile__user').all():
        profile = getattr(document, 'employee_profile', None)
        if profile and profile.user_id:
            document.user_id = profile.user_id
            document.save(update_fields=['user'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('employees', '0002_employeedepartmentrole_employeedocument_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='employeedocument',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='employee_documents', to=settings.AUTH_USER_MODEL),
        ),
        migrations.RunPython(copy_document_owner_to_user, noop_reverse),
        migrations.RemoveField(
            model_name='employeedocument',
            name='employee_profile',
        ),
        migrations.AlterField(
            model_name='employeedocument',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employee_documents', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddIndex(
            model_name='employeedocument',
            index=models.Index(fields=['user'], name='employees_e_user_id_9d2de1_idx'),
        ),
    ]
