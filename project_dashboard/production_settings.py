
"""
Production settings entry point.
Uses the same configuration as project_dashboard.settings (single settings module).
"""
from .settings import *  # noqa: F401, F403

# Production must never expose Django debug pages unless explicitly changed in code.
DEBUG = False
