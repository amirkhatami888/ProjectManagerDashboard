from django.core.management.base import BaseCommand

from ai_assistant import snapshots


class Command(BaseCommand):
    help = "بازسازی JSON snapshotهای طرح/پروژه/زیرپروژه برای دستیار"

    def handle(self, *args, **options):
        index = snapshots.rebuild_all()
        self.stdout.write(self.style.SUCCESS(
            f"بازسازی شد: {len(index['programs'])} طرح + پروژه/زیرپروژه‌های آن‌ها"))
