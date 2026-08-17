import json
from pathlib import Path

from django.core.management.base import BaseCommand

from creator_project.models import ProjectFinancialAllocation
from creator_subproject.models import AdjustmentSituationReport, FinancialDocument, SituationReport, SubProject


class Command(BaseCommand):
    help = "مقایسهٔ enumها و fieldهای کلیدی مدل با قرارداد پایگاه دانش دستیار"

    def handle(self, *args, **options):
        path = Path(__file__).resolve().parents[2] / "knowledge" / "schema.json"
        schema = json.loads(path.read_text(encoding="utf-8"))
        checks = [
            (SubProject, "SubProject", ("project_stage", "state", "contract_type", "execution_method")),
            (ProjectFinancialAllocation, "ProjectFinancialAllocation", ("amount", "allocation_type")),
            (FinancialDocument, "FinancialDocument", ("document_number", "contractor_date", "contractor_submit_date")),
            (SituationReport, "SituationReport", ("payment_amount_field", "allocation_type")),
            (AdjustmentSituationReport, "AdjustmentSituationReport", ("payment_amount_field",)),
        ]
        errors = []
        for model, name, fields in checks:
            documented = schema["models"].get(name, {})
            for field in fields:
                if not hasattr(model, field) and field not in documented.values():
                    errors.append(f"{name}.{field}")
        if errors:
            self.stdout.write(self.style.ERROR("فیلدهای مستندنشده: " + ", ".join(errors)))
            raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS("قرارداد پایگاه دانش با fieldهای کلیدی مدل همخوان است."))
