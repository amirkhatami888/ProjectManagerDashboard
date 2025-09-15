from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
import json

@login_required
def session_info(request):
    """Get current session information"""
    session_key = request.session.session_key
    session_data = {
        'session_key': session_key,
        'user_id': request.user.id,
        'username': request.user.username,
        'last_activity': timezone.now().isoformat(),
        'is_authenticated': request.user.is_authenticated,
    }
    return JsonResponse(session_data)

@login_required
def active_sessions(request):
    """Get all active sessions for the current user"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    active_sessions = []
    
    for session in sessions:
        try:
            session_data = session.get_decoded()
            if 'user_id' in session_data:
                user = User.objects.get(id=session_data['user_id'])
                active_sessions.append({
                    'session_key': session.session_key,
                    'username': user.username,
                    'expire_date': session.expire_date.isoformat(),
                })
        except (User.DoesNotExist, KeyError):
            continue
    
    return JsonResponse({'active_sessions': active_sessions})

@require_http_methods(["POST"])
@login_required
def terminate_session(request):
    """Terminate a specific session"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        session_key = data.get('session_key')
        
        if session_key:
            Session.objects.filter(session_key=session_key).delete()
            return JsonResponse({'success': True, 'message': 'Session terminated'})
        else:
            return JsonResponse({'error': 'Session key required'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)