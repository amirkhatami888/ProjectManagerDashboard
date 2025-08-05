import hmac
import hashlib
import subprocess
import os
import logging
from django.conf import settings
from django.utils import timezone
from .models import WebhookEvent, WebhookConfiguration

logger = logging.getLogger(__name__)


def verify_github_signature(payload_body, signature_header, secret_token):
    """
    Verify that the webhook came from GitHub using the secret token
    """
    if not signature_header or not secret_token:
        return False
    
    # GitHub sends the signature as "sha256=..."
    if not signature_header.startswith('sha256='):
        return False
    
    expected_signature = signature_header[7:]  # Remove 'sha256=' prefix
    
    # Create the expected signature
    calculated_signature = hmac.new(
        secret_token.encode('utf-8'),
        payload_body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, calculated_signature)


def parse_github_event(payload):
    """
    Parse GitHub webhook payload and extract relevant information
    """
    event_data = {
        'event_type': 'other',
        'repository': '',
        'branch': '',
        'commit_sha': '',
        'commit_message': '',
    }
    
    try:
        # Handle push events
        if 'ref' in payload and payload['ref'].startswith('refs/heads/'):
            event_data['event_type'] = 'push'
            event_data['branch'] = payload['ref'].replace('refs/heads/', '')
            event_data['repository'] = payload['repository']['full_name']
            
            if 'head_commit' in payload and payload['head_commit']:
                event_data['commit_sha'] = payload['head_commit']['id']
                event_data['commit_message'] = payload['head_commit']['message']
        
        # Handle pull request events
        elif 'pull_request' in payload:
            event_data['event_type'] = 'pull_request'
            event_data['repository'] = payload['repository']['full_name']
            event_data['branch'] = payload['pull_request']['head']['ref']
            event_data['commit_sha'] = payload['pull_request']['head']['sha']
            event_data['commit_message'] = f"PR #{payload['pull_request']['number']}: {payload['pull_request']['title']}"
        
        # Handle release events
        elif 'release' in payload:
            event_data['event_type'] = 'release'
            event_data['repository'] = payload['repository']['full_name']
            event_data['commit_message'] = f"Release: {payload['release']['name']}"
        
        # Handle issues events
        elif 'issue' in payload:
            event_data['event_type'] = 'issues'
            event_data['repository'] = payload['repository']['full_name']
            event_data['commit_message'] = f"Issue #{payload['issue']['number']}: {payload['issue']['title']}"
    
    except Exception as e:
        logger.error(f"Error parsing GitHub event: {e}")
    
    return event_data


def deploy_repository(repository_url, branch='main'):
    """
    Deploy the repository by pulling the latest changes
    """
    try:
        # Get the project root directory
        project_root = settings.BASE_DIR
        
        # Check if we're in a git repository
        if not os.path.exists(os.path.join(project_root, '.git')):
            logger.error("Not in a git repository")
            return False, "Not in a git repository"
        
        # Fetch the latest changes
        fetch_result = subprocess.run(
            ['git', 'fetch', 'origin'],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        if fetch_result.returncode != 0:
            logger.error(f"Git fetch failed: {fetch_result.stderr}")
            return False, f"Git fetch failed: {fetch_result.stderr}"
        
        # Checkout the specified branch
        checkout_result = subprocess.run(
            ['git', 'checkout', branch],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        if checkout_result.returncode != 0:
            logger.error(f"Git checkout failed: {checkout_result.stderr}")
            return False, f"Git checkout failed: {checkout_result.stderr}"
        
        # Pull the latest changes
        pull_result = subprocess.run(
            ['git', 'pull', 'origin', branch],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        if pull_result.returncode != 0:
            logger.error(f"Git pull failed: {pull_result.stderr}")
            return False, f"Git pull failed: {pull_result.stderr}"
        
        # Run migrations if needed
        migrate_result = subprocess.run(
            ['python', 'manage.py', 'migrate'],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        if migrate_result.returncode != 0:
            logger.warning(f"Migration failed: {migrate_result.stderr}")
            # Don't fail the deployment for migration issues
        
        # Collect static files
        collect_static_result = subprocess.run(
            ['python', 'manage.py', 'collectstatic', '--noinput'],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        if collect_static_result.returncode != 0:
            logger.warning(f"Collect static failed: {collect_static_result.stderr}")
            # Don't fail the deployment for static collection issues
        
        logger.info(f"Successfully deployed {repository_url} branch {branch}")
        return True, "Deployment completed successfully"
        
    except Exception as e:
        logger.error(f"Deployment error: {e}")
        return False, str(e)


def process_webhook_event(event_data, payload):
    """
    Process a webhook event and trigger deployment if needed
    """
    try:
        # Create webhook event record
        webhook_event = WebhookEvent.objects.create(
            event_type=event_data['event_type'],
            event_id=f"{event_data['repository']}-{timezone.now().timestamp()}",
            repository=event_data['repository'],
            branch=event_data['branch'],
            commit_sha=event_data['commit_sha'],
            commit_message=event_data['commit_message'],
            payload=payload
        )
        
        # Check if auto-deploy is enabled for this repository
        config = WebhookConfiguration.objects.filter(
            repository_url__icontains=event_data['repository'],
            is_active=True,
            auto_deploy=True
        ).first()
        
        if not config:
            logger.info(f"No auto-deploy configuration found for {event_data['repository']}")
            webhook_event.mark_as_completed()
            return True, "No auto-deploy configuration found"
        
        # Check if this is the correct branch for deployment
        if event_data['branch'] != config.deploy_branch:
            logger.info(f"Event for branch {event_data['branch']}, deploying {config.deploy_branch}")
            webhook_event.mark_as_completed()
            return True, f"Event for different branch ({event_data['branch']})"
        
        # Mark as processing
        webhook_event.mark_as_processing()
        
        # Perform deployment
        success, message = deploy_repository(config.repository_url, config.deploy_branch)
        
        if success:
            webhook_event.mark_as_completed()
        else:
            webhook_event.mark_as_failed(message)
        
        return success, message
        
    except Exception as e:
        logger.error(f"Error processing webhook event: {e}")
        return False, str(e) 