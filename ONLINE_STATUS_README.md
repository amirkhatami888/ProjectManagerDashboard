# Online/Offline Status System

## Overview

The activity monitoring system now includes enhanced online/offline status tracking based on user sessions. This system provides real-time monitoring of user activity with automatic session timeout management.

## Features

### 1. Session-Based Online Status
- Users are considered "online" if they have an active session with recent activity
- Sessions automatically timeout after 15 minutes of inactivity
- Real-time status updates via AJAX

### 2. Enhanced User Activity Report
- Shows accurate online/offline status for all users
- Displays time since last activity
- Session duration tracking
- Real-time updates every 30 seconds

### 3. Automatic Session Management
- Automatic cleanup of expired sessions
- Session timeout detection
- Periodic cleanup in middleware

## Technical Implementation

### Models

#### UserSession Model Enhancements
```python
class UserSession(models.Model):
    # ... existing fields ...
    
    # Session timeout (15 minutes default)
    SESSION_TIMEOUT_MINUTES = 15
    
    @property
    def is_online(self):
        """Check if user is currently online based on session timeout"""
        if not self.is_active:
            return False
        
        # Check if session has timed out (15 minutes of inactivity)
        timeout_threshold = timezone.now() - timedelta(minutes=self.SESSION_TIMEOUT_MINUTES)
        return self.last_activity > timeout_threshold
```

### Utility Functions

#### cleanup_expired_sessions()
- Automatically marks expired sessions as inactive
- Returns count of cleaned sessions
- Called periodically by middleware

#### get_user_online_status(user)
- Returns detailed online status for a specific user
- Includes session duration and last activity time
- Handles edge cases gracefully

#### get_all_online_users()
- Returns list of all currently online users
- Automatically cleans up expired sessions first
- Includes session details for each user

### API Endpoints

#### GET /activity-monitor/api/online-status/
Returns real-time online status for all users:
```json
{
    "success": true,
    "online_users": [
        {
            "user_id": 1,
            "username": "user1",
            "last_activity": "2024-01-01T10:30:00Z",
            "session_duration": "0:15:30",
            "time_since_last_activity": "0:02:15",
            "is_online": true
        }
    ],
    "total_online": 1,
    "timestamp": "2024-01-01T10:32:15Z"
}
```

#### GET /activity-monitor/api/user-activity-summary/
Returns summary statistics:
```json
{
    "success": true,
    "total_users": 50,
    "online_users": 5,
    "today_activities": 150,
    "timestamp": "2024-01-01T10:32:15Z"
}
```

## Usage

### Viewing Online Status

1. Navigate to **نظارت بر فعالیت‌ها** → **گزارش فعالیت‌ها**
2. The page shows real-time online/offline status for all users
3. Status updates automatically every 30 seconds
4. Green dot indicates online users, gray dot indicates offline users

### Management Commands

#### Clean up expired sessions manually:
```bash
python manage.py cleanup_sessions
```

#### Dry run to see what would be cleaned:
```bash
python manage.py cleanup_sessions --dry-run
```

#### Custom timeout (e.g., 30 minutes):
```bash
python manage.py cleanup_sessions --timeout 30
```

### Testing

Run the test script to verify functionality:
```bash
python test_online_status.py
```

## Configuration

### Session Timeout
Default timeout is 15 minutes. To change this:

1. Update `SESSION_TIMEOUT_MINUTES` in `UserSession` model
2. Update the timeout in `cleanup_expired_sessions()` function
3. Update the management command default

### Auto-refresh Interval
The frontend updates every 30 seconds. To change this:

1. Update the `setInterval` call in the JavaScript
2. Update the page reload timeout

## Monitoring

### Logs
Session cleanup activities are logged to the console. Check for:
- Session cleanup counts
- Error messages during cleanup
- Session timeout events

### Database Queries
Monitor these queries for performance:
- `UserSession.objects.filter(is_active=True)`
- `UserSession.objects.filter(last_activity__lt=timeout_threshold)`

## Troubleshooting

### Users showing as offline when they should be online
1. Check if sessions are being properly tracked
2. Verify session timeout settings
3. Check middleware is active
4. Run manual session cleanup

### Performance issues
1. Monitor database query performance
2. Consider reducing cleanup frequency
3. Add database indexes if needed
4. Monitor session table size

### Real-time updates not working
1. Check JavaScript console for errors
2. Verify API endpoints are accessible
3. Check network connectivity
4. Verify user permissions

## Future Enhancements

1. **WebSocket Support**: Real-time updates without polling
2. **Custom Timeouts**: Per-user or per-role timeout settings
3. **Activity Tracking**: More granular activity monitoring
4. **Notifications**: Alerts when users go online/offline
5. **Analytics**: Session duration and activity patterns
