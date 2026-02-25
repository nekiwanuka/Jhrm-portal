from django.db import migrations


def backfill_notice_author_snapshot(apps, schema_editor):
    Notice = apps.get_model('noticeboard', 'Notice')
    User = apps.get_model('accounts', 'User')
    EmployeeProfile = apps.get_model('employees', 'EmployeeProfile')
    Department = apps.get_model('employees', 'Department')
    Position = apps.get_model('employees', 'Position')

    notice_ids = list(
        Notice.objects.exclude(created_by_id__isnull=True)
        .filter(created_by_name='')
        .values_list('id', flat=True)
    )
    if not notice_ids:
        return

    user_ids = set(
        Notice.objects.filter(id__in=notice_ids)
        .exclude(created_by_id__isnull=True)
        .values_list('created_by_id', flat=True)
    )
    if not user_ids:
        return

    users = {
        row['id']: row
        for row in User.objects.filter(id__in=user_ids).values(
            'id', 'first_name', 'last_name', 'username', 'phone_number'
        )
    }

    profiles = {
        row['user_id']: row
        for row in EmployeeProfile.objects.filter(user_id__in=user_ids).values(
            'user_id', 'department_id', 'position_id'
        )
    }

    department_ids = {row['department_id'] for row in profiles.values() if row['department_id']}
    position_ids = {row['position_id'] for row in profiles.values() if row['position_id']}

    departments = dict(Department.objects.filter(id__in=department_ids).values_list('id', 'name'))
    positions = dict(Position.objects.filter(id__in=position_ids).values_list('id', 'title'))

    to_update = []
    for notice in Notice.objects.filter(id__in=notice_ids):
        user = users.get(notice.created_by_id)
        if not user:
            continue

        full_name = f"{(user.get('first_name') or '').strip()} {(user.get('last_name') or '').strip()}".strip()
        notice.created_by_name = full_name or user.get('username') or ''
        notice.created_by_phone = user.get('phone_number') or ''

        profile = profiles.get(notice.created_by_id)
        if profile:
            notice.created_by_department = departments.get(profile.get('department_id'), '') if profile.get('department_id') else ''
            notice.created_by_position = positions.get(profile.get('position_id'), '') if profile.get('position_id') else ''

        to_update.append(notice)

    if to_update:
        Notice.objects.bulk_update(
            to_update,
            ['created_by_name', 'created_by_phone', 'created_by_department', 'created_by_position'],
            batch_size=500,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0004_rename_employees_e_user_id_9d2de1_idx_employees_e_user_id_1e9249_idx_and_more'),
        ('noticeboard', '0002_notice_created_by_department_notice_created_by_name_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_notice_author_snapshot, migrations.RunPython.noop),
    ]
