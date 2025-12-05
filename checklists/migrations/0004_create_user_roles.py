from django.db import migrations

def create_roles(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    roles = ["Manager", "Supervisor", "Bartender", "Security"]

    for role in roles:
        Group.objects.get_or_create(name=role)

class Migration(migrations.Migration):

    dependencies = [
        ('checklists', '0001_initial'),  # change 0001_initial to your latest migration
    ]

    operations = [
        migrations.RunPython(create_roles),
    ]
