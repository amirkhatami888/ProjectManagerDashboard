from django.core.management.base import BaseCommand
from django.utils import timezone

from ai_assistant.models import AIAutomationRule
from ai_assistant.domain_tools import project_health_check
from ai_assistant.permissions import visible_projects
from accounts.models import User


class Command(BaseCommand):
    help = "Run active AI project monitoring rules and persist auditable results."

    def add_arguments(self, parser):
        parser.add_argument("--rule", type=int)
        parser.add_argument("--user", type=int, help="User whose visibility scope is used")

    def handle(self, *args, **options):
        rules = AIAutomationRule.objects.filter(is_active=True)
        if options.get("rule"):
            rules = rules.filter(pk=options["rule"])
        user = User.objects.filter(pk=options.get("user")).first() if options.get("user") else User.objects.filter(is_staff=True).first()
        if not user:
            self.stderr.write("No staff user available for visibility scope")
            return
        for rule in rules:
            config = rule.config or {}
            ids = config.get("project_ids") or list(visible_projects(user).values_list("pk", flat=True))
            results = []
            for project_id in ids[: int(config.get("max_projects", 200))]:
                try:
                    result = project_health_check(user, int(project_id), config.get("progress_threshold", 25))
                    if result["health"] != "سبز" or config.get("include_green"):
                        results.append(result)
                except Exception as exc:
                    results.append({"project_id": project_id, "health": "خطا", "error": str(exc)[:300]})
            rule.last_result = {"run_at": timezone.now().isoformat(), "projects": results, "count": len(results)}
            rule.last_run_at = timezone.now()
            rule.save(update_fields=["last_result", "last_run_at"])
            self.stdout.write(self.style.SUCCESS(f"{rule.name}: {len(results)} findings"))
