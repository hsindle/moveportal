from django.core.management.base import BaseCommand
from checklists.models import ChecklistTemplate, ChecklistSession
from checklists.utils.operational_day import get_operational_date
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Generates daily checklist sessions for the new operational day."

    def handle(self, *args, **kwargs):
        User = get_user_model()

        # You may want a default "system" user
        system_user, _ = User.objects.get_or_create(username="system")

        today = get_operational_date()

        for template in ChecklistTemplate.objects.filter(is_active=True):

            exists = ChecklistSession.objects.filter(
                template=template,
                date=today
            ).exists()

            if not exists:
                ChecklistSession.objects.create(
                    template=template,
                    shift_name="Default Shift",
                    date=today,
                    created_by=system_user
                )

        self.stdout.write(self.style.SUCCESS(
            f"Checklist generation complete for operational day {today}"
        ))
