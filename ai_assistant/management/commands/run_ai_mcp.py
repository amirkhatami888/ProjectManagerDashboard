from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "اجرای سرور MCP دستیار برای ابزارهای جستجوی گزارش‌گیر (stdio)"

    def handle(self, *args, **options):
        from ai_assistant.mcp_server import mcp
        mcp.run()
