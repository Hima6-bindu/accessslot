# Generated migration to create default usage limits

from django.db import migrations


def create_default_limits(apps, schema_editor):
    """Create default usage limits for STUDENT and FACULTY roles."""
    UsageLimit = apps.get_model('equipment', 'UsageLimit')
    
    # Create default limits
    UsageLimit.objects.get_or_create(
        role='STUDENT',
        defaults={'max_weekly_hours': 4}
    )
    UsageLimit.objects.get_or_create(
        role='FACULTY',
        defaults={'max_weekly_hours': 8}
    )


def remove_default_limits(apps, schema_editor):
    """Remove default usage limits."""
    UsageLimit = apps.get_model('equipment', 'UsageLimit')
    UsageLimit.objects.filter(role__in=['STUDENT', 'FACULTY']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('equipment', '0002_usagelimit_booking'),
    ]

    operations = [
        migrations.RunPython(create_default_limits, remove_default_limits),
    ]
