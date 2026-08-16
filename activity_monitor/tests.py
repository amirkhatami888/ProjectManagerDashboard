from django.template.loader import get_template
from django.test import SimpleTestCase


class ActivityMonitorTemplateTests(SimpleTestCase):
    def test_activity_log_detail_template_exists(self):
        template = get_template('activity_monitor/activity_log_detail.html')

        self.assertIsNotNone(template)
