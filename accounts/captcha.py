"""
CAPTCHA System for Django Login Protection
Simple mathematical CAPTCHA to prevent automated brute-force attacks
"""
import random
import hashlib
import time
from django.core.cache import cache
from django.conf import settings

class SimpleCaptcha:
    """Simple mathematical CAPTCHA system"""
    
    def __init__(self):
        self.cache_timeout = getattr(settings, 'CAPTCHA_CACHE_TIMEOUT', 300)  # 5 minutes
    
    def generate_captcha(self, session_key):
        """Generate a new CAPTCHA challenge"""
        # Generate simple math problem
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        operation = random.choice(['+', '-', '*'])
        
        if operation == '+':
            answer = num1 + num2
            question = f"{num1} + {num2}"
        elif operation == '-':
            # Ensure positive result
            if num1 < num2:
                num1, num2 = num2, num1
            answer = num1 - num2
            question = f"{num1} - {num2}"
        else:  # multiplication
            answer = num1 * num2
            question = f"{num1} × {num2}"
        
        # Create unique ID for this CAPTCHA
        captcha_id = hashlib.md5(f"{session_key}{time.time()}{random.random()}".encode()).hexdigest()[:8]
        
        # Store answer in cache
        cache_key = f"captcha_answer:{captcha_id}"
        cache.set(cache_key, answer, self.cache_timeout)
        
        return {
            'id': captcha_id,
            'question': question,
            'answer': answer  # For testing purposes only
        }
    
    def verify_captcha(self, captcha_id, user_answer):
        """Verify CAPTCHA answer"""
        if not captcha_id or not user_answer:
            return False
        
        try:
            user_answer = int(user_answer.strip())
        except (ValueError, AttributeError):
            return False
        
        cache_key = f"captcha_answer:{captcha_id}"
        correct_answer = cache.get(cache_key)
        
        if correct_answer is None:
            return False  # CAPTCHA expired or invalid
        
        # Clear the answer after verification
        cache.delete(cache_key)
        
        return user_answer == correct_answer
    
    def cleanup_expired_captchas(self):
        """Clean up expired CAPTCHAs (called periodically)"""
        # This would be implemented with a more sophisticated cleanup
        # For now, we rely on cache expiration
        pass




