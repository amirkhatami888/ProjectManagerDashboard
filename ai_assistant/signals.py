"""Keep AI snapshots in sync with the authoritative models.

Connecting from ai_assistant (which is installed and has a ready() hook) keeps
sync logic out of the creator_* apps while still firing on every save/delete.
Regeneration is best-effort: a failure must never break the underlying write.
"""
import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from creator_program.models import Program
from creator_project.models import Project
from creator_subproject.models import SubProject

from . import snapshots

logger = logging.getLogger("ai_assistant")


@receiver(post_save, sender=Program, dispatch_uid="ai_snap_program_save")
@receiver(post_delete, sender=Program, dispatch_uid="ai_snap_program_del")
def _sync_program(sender, instance, **kwargs):
    try:
        snapshots.rebuild_all()
    except Exception:
        logger.exception("Snapshot sync failed (program %s)", instance.pk)


@receiver(post_save, sender=Project, dispatch_uid="ai_snap_project_save")
@receiver(post_delete, sender=Project, dispatch_uid="ai_snap_project_del")
def _sync_project(sender, instance, **kwargs):
    try:
        if instance.program_id:
            snapshots.write_program_snapshot(instance.program_id)
        snapshots.rebuild_index()
    except Exception:
        logger.exception("Snapshot sync failed (project %s)", instance.pk)


@receiver(post_save, sender=SubProject, dispatch_uid="ai_snap_subproject_save")
@receiver(post_delete, sender=SubProject, dispatch_uid="ai_snap_subproject_del")
def _sync_subproject(sender, instance, **kwargs):
    try:
        project = instance.project
        if project:
            snapshots.write_subproject_snapshot(instance.pk)
            snapshots.write_project_snapshot(project.pk)
            if project.program_id:
                snapshots.write_program_snapshot(project.program_id)
            snapshots.rebuild_index()
    except Exception:
        logger.exception("Snapshot sync failed (subproject %s)", instance.pk)


def connect_snapshot_signals():
    """Idempotent wiring; safe to call multiple times during tests."""
    post_save.connect(_sync_program, sender=Program, dispatch_uid="ai_snap_program_save")
    post_save.connect(_sync_project, sender=Project, dispatch_uid="ai_snap_project_save")
    post_save.connect(_sync_subproject, sender=SubProject, dispatch_uid="ai_snap_subproject_save")
    post_delete.connect(_sync_program, sender=Program, dispatch_uid="ai_snap_program_del")
    post_delete.connect(_sync_project, sender=Project, dispatch_uid="ai_snap_project_del")
    post_delete.connect(_sync_subproject, sender=SubProject, dispatch_uid="ai_snap_subproject_del")
