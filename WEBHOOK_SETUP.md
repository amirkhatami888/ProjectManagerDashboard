# GitHub Webhook Setup Guide

This guide explains how to set up and use the GitHub webhook system for automatic deployment of your Django project.

## Overview

The webhook system allows your Django server to automatically receive notifications from GitHub when code changes are pushed, and optionally trigger automatic deployments.

## Features

- **GitHub Webhook Integration**: Receive webhook events from GitHub
- **Automatic Deployment**: Pull latest changes and run migrations
- **Event Logging**: Track all webhook events with detailed information
- **Security**: Verify webhook signatures using secret tokens
- **Dashboard**: Web interface to manage webhook configurations and view events
- **Filtering**: Filter and search webhook events by type, status, and repository

## Setup Instructions

### 1. Install Dependencies

The webhook system requires the `cryptography` package for signature verification:

```bash
pip install cryptography
```

### 2. Database Migration

Run the migrations to create the webhook tables:

```bash
python manage.py migrate
```

### 3. Create Webhook Configuration

1. Go to your Django admin panel: `http://your-domain/admin/`
2. Navigate to "Webhook Configurations" under the "Webhooks" section
3. Click "Add Webhook Configuration"
4. Fill in the configuration:
   - **Repository URL**: Your GitHub repository URL (e.g., `https://github.com/username/repo`)
   - **Secret Token**: (Optional) A secret token for webhook verification
   - **Deploy Branch**: The branch to deploy from (default: `main`)
   - **Active**: Enable/disable this webhook
   - **Auto Deploy**: Enable automatic deployment when webhook is received

### 4. Configure GitHub Webhook

1. Go to your GitHub repository
2. Navigate to **Settings** → **Webhooks**
3. Click **"Add webhook"**
4. Configure the webhook:
   - **Payload URL**: `https://your-domain.com/webhooks/github/`
   - **Content type**: `application/json`
   - **Secret**: (Optional) Enter the same secret token you used in the Django configuration
   - **Events**: Select the events you want to receive:
     - ✅ **Push** (recommended for deployments)
     - ✅ **Pull requests** (optional)
     - ✅ **Releases** (optional)
     - ✅ **Issues** (optional)
5. Click **"Add webhook"**

### 5. Test the Webhook

You can test the webhook functionality using the management command:

```bash
python manage.py test_webhook --event-type push
```

Or test with a specific repository:

```bash
python manage.py test_webhook --repository https://github.com/username/repo --event-type pull_request
```

## Usage

### Webhook Dashboard

Access the webhook dashboard at: `http://your-domain.com/webhooks/dashboard/`

The dashboard shows:
- Statistics (total events, successful, failed, pending)
- Recent webhook events
- Webhook configurations
- Quick access to management features

### Managing Webhook Events

- **View All Events**: `http://your-domain.com/webhooks/events/`
- **Filter Events**: Filter by event type, status, or repository
- **Event Details**: Click on any event to view detailed information

### Managing Configurations

- **List Configurations**: `http://your-domain.com/webhooks/configurations/`
- **Create Configuration**: Add new webhook configurations
- **Edit Configuration**: Modify existing configurations
- **Delete Configuration**: Remove webhook configurations

## How It Works

### 1. Webhook Reception

When GitHub sends a webhook to your server:

1. The webhook endpoint (`/webhooks/github/`) receives the POST request
2. The system verifies the webhook signature (if a secret token is configured)
3. The event data is parsed and stored in the database
4. If auto-deploy is enabled, the deployment process begins

### 2. Deployment Process

For each webhook event:

1. **Git Operations**:
   - Fetch latest changes from the remote repository
   - Checkout the specified branch
   - Pull the latest changes

2. **Django Operations**:
   - Run database migrations (`python manage.py migrate`)
   - Collect static files (`python manage.py collectstatic --noinput`)

3. **Status Tracking**:
   - Mark event as "processing" during deployment
   - Mark as "completed" on success or "failed" on error
   - Store error messages if deployment fails

### 3. Security Features

- **Signature Verification**: Uses HMAC-SHA256 to verify webhook authenticity
- **CSRF Protection**: Webhook endpoint is exempt from CSRF protection
- **Staff Access**: Management interface requires staff permissions

## Configuration Options

### Webhook Configuration Fields

- **Repository URL**: The GitHub repository URL
- **Secret Token**: Optional secret for webhook verification
- **Active**: Enable/disable this webhook configuration
- **Auto Deploy**: Enable automatic deployment on webhook events
- **Deploy Branch**: The branch to deploy from (default: `main`)

### Event Types Supported

- **Push**: Code pushes to any branch
- **Pull Request**: Pull request events (opened, closed, merged)
- **Release**: Release creation events
- **Issues**: Issue events (opened, closed, etc.)

### Event Statuses

- **Pending**: Event received, waiting to be processed
- **Processing**: Event is currently being processed
- **Completed**: Event processed successfully
- **Failed**: Event processing failed

## Troubleshooting

### Common Issues

1. **Webhook Not Receiving Events**:
   - Check that the webhook URL is accessible from the internet
   - Verify the webhook is active in GitHub
   - Check server logs for errors

2. **Deployment Fails**:
   - Ensure the server has git access to the repository
   - Check that the specified branch exists
   - Verify the server has write permissions to the project directory

3. **Signature Verification Fails**:
   - Ensure the secret token matches between GitHub and Django
   - Check that the webhook is using the correct content type

### Debugging

1. **Check Webhook Events**: View events in the Django admin or webhook dashboard
2. **Server Logs**: Check Django logs for webhook processing errors
3. **GitHub Webhook Logs**: View delivery logs in GitHub repository settings

## Security Considerations

1. **Use HTTPS**: Always use HTTPS for webhook URLs in production
2. **Secret Tokens**: Use strong secret tokens for webhook verification
3. **Access Control**: Ensure only authorized users can access webhook management
4. **Rate Limiting**: Consider implementing rate limiting for webhook endpoints
5. **Logging**: Monitor webhook events for suspicious activity

## API Endpoints

### Webhook Endpoint

- **URL**: `/webhooks/github/`
- **Method**: POST
- **Authentication**: None (public endpoint)
- **Content-Type**: application/json

### Management Endpoints

All management endpoints require staff authentication:

- `/webhooks/dashboard/` - Webhook dashboard
- `/webhooks/events/` - List webhook events
- `/webhooks/events/<id>/` - Event details
- `/webhooks/configurations/` - List configurations
- `/webhooks/configurations/create/` - Create configuration
- `/webhooks/configurations/<id>/edit/` - Edit configuration
- `/webhooks/configurations/<id>/delete/` - Delete configuration

## Development

### Adding New Event Types

1. Add the event type to `WebhookEvent.EVENT_TYPES`
2. Update the `parse_github_event` function in `utils.py`
3. Add corresponding template logic

### Customizing Deployment

Modify the `deploy_repository` function in `utils.py` to add custom deployment steps.

### Testing

Use the management command to test webhook functionality:

```bash
python manage.py test_webhook --event-type push
```

## Support

For issues or questions about the webhook system:

1. Check the webhook dashboard for event status
2. Review server logs for error messages
3. Verify GitHub webhook configuration
4. Test with the management command

---

**Note**: This webhook system is designed for automatic deployment of Django applications. Ensure your server environment is properly configured for git operations and Django management commands. 