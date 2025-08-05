import requests
import json
import logging
import time
import random
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from .models import SMSProvider, SMSLog, SMSTemplate, SMSSettings

# Import IPPanel SDK
try:
    from ippanel import Client
    from ippanel import HTTPError, Error, ResponseCode
    IPPANEL_AVAILABLE = True
except ImportError:
    IPPANEL_AVAILABLE = False
    print("IPPanel SDK not installed. Install with: pip install ippanel")

logger = logging.getLogger(__name__)

class IPPanelSMSSender:
    """Utility class for sending SMS messages through IPPanel API using the official SDK"""
    
    @classmethod
    def get_settings(cls):
        """Get the current SMS settings"""
        settings = SMSSettings.get_settings()
        if not settings.provider:
            logger.error("No active SMS provider set in settings")
            return None
        return settings
    
    @classmethod
    def get_credit(cls):
        """Get remaining credit from IPPanel"""
        sms_settings = cls.get_settings()
        if not sms_settings or not sms_settings.provider:
            return {"status": "ERROR", "message": "No SMS provider configured"}
        
        provider = sms_settings.provider
        
        if not IPPANEL_AVAILABLE:
            return {"status": "ERROR", "message": "IPPanel SDK not installed"}
        
        try:
            # Create client instance
            sms = Client(provider.api_key)
            credit = sms.get_credit()
            
            return {
                "status": "OK",
                "credit": credit,
                "message": f"Credit: {credit}"
            }
        except Error as e:
            logger.error(f"IPPanel error getting credit: {e.code}, {e.message}")
            return {"status": "ERROR", "message": f"Error: {e.message}"}
        except HTTPError as e:
            logger.error(f"HTTP error getting credit: {e}")
            return {"status": "ERROR", "message": f"HTTP Error: {e}"}
        except Exception as e:
            logger.error(f"Unexpected error getting credit: {e}")
            return {"status": "ERROR", "message": f"Unexpected error: {e}"}
    
    @classmethod
    def send_sms(cls, recipient_number, message, sender_user=None, recipient_user=None, template=None):
        """
        Send an SMS to a single recipient using IPPanel SDK
        
        Args:
            recipient_number: The phone number to send to
            message: The message content
            sender_user: The user sending the message (optional)
            recipient_user: The user receiving the message (optional)
            template: The template used for the message (optional)
            
        Returns:
            dict: Response with status and message
        """
        from notifications_sms.models import SMSLog
        
        # Get settings
        sms_settings = cls.get_settings()
        if not sms_settings or not sms_settings.provider:
            logger.error("No SMS provider configured")
            
            # Log the failed attempt
            log = SMSLog.objects.create(
                sender=sender_user,
                recipient_number=recipient_number,
                recipient_user=recipient_user,
                message=message,
                template=template,
                status='FAILED',
                error_message="No SMS provider configured"
            )
            
            return {"status": "ERROR", "message": "No SMS provider configured"}
        
        provider = sms_settings.provider
        
        if not IPPANEL_AVAILABLE:
            logger.error("IPPanel SDK not installed")
            
            # Log the failed attempt
            log = SMSLog.objects.create(
                sender=sender_user,
                recipient_number=recipient_number,
                recipient_user=recipient_user,
                message=message,
                template=template,
                status='FAILED',
                error_message="IPPanel SDK not installed"
            )
            
            return {"status": "ERROR", "message": "IPPanel SDK not installed"}
        
        # Check if this is a test/demo provider (by API key)
        logger.info(f"Checking API key for simulation: '{provider.api_key[:20]}...'")
        if provider.api_key == 'your-api-key-here' or provider.api_key.startswith('test-'):
            logger.info("Using simulation mode for SMS sending")
            # Simulate SMS sending for testing
            message_id = f"sim_{int(time.time())}_{random.randint(1000, 9999)}"
            
            # Log the simulated send
            log = SMSLog.objects.create(
                sender=sender_user,
                recipient_number=recipient_number,
                recipient_user=recipient_user,
                message=message,
                template=template,
                status='SENT',
                message_id=message_id,
                provider=provider
            )
            
            logger.info(f"Simulated SMS sent to {recipient_number}: {message[:50]}...")
            
            return {
                "status": "OK", 
                "message_id": message_id,
                "note": "This is a simulated SMS for testing purposes"
            }
        
        logger.info("Using real IPPanel API")
        print(f"Using real IPPanel API for {recipient_number}")
        
        # Format the phone number (remove any + prefix and ensure it starts with proper country code)
        recipient_number = recipient_number.strip()
        if recipient_number.startswith('+'):
            recipient_number = recipient_number[1:]
        
        # Ensure number starts with country code (assuming Iran's country code 98)
        if not recipient_number.startswith('98') and recipient_number.startswith('0'):
            recipient_number = '98' + recipient_number[1:]
        
        # Use sender number from provider settings or default
        originator = provider.sender_number if provider.sender_number else "+985000404223"
        
        # Create log entry before trying to send
        log = SMSLog.objects.create(
            sender=sender_user,
            recipient_number=recipient_number,
            recipient_user=recipient_user,
            message=message,
            template=template,
            status='PENDING',
            provider=provider
        )
        
        try:
            # Create client instance
            sms = Client(provider.api_key)
            
            # Log the request details for debugging
            logger.info(f"Sending SMS to: {recipient_number}")
            logger.info(f"Originator: {originator}")
            logger.info(f"Message length: {len(message)}")
            print(f"Sending SMS to: {recipient_number}")
            print(f"Originator: {originator}")
            print(f"Message: {message[:50]}...")
            
            # Send the SMS using IPPanel SDK
            message_id = sms.send(
                originator,           # originator
                [recipient_number],   # recipients
                message,              # message
                "SMS sent from Dashboard"  # description
            )
            
            # Update log entry
            log.status = 'SENT'
            log.message_id = message_id
            log.save()
                    
            logger.info(f"SMS sent successfully to {recipient_number}. Message ID: {message_id}")
            print(f"SMS sent successfully to {recipient_number}. Message ID: {message_id}")
            
            return {
                "status": "OK", 
                "message_id": message_id,
                "message": "SMS sent successfully"
            }
            
        except Error as e:
            # IPPanel SMS error
            error_msg = f"IPPanel error: {e.code}, {e.message}"
            logger.error(error_msg)
            print(error_msg)
            
            # Handle specific error cases
            if e.code == ResponseCode.ErrUnprocessableEntity.value:
                error_details = []
                for field in e.message:
                    error_details.append(f"Field: {field}, Errors: {e.message[field]}")
                error_msg = f"Validation error: {'; '.join(error_details)}"
            
            log.status = 'FAILED'
            log.error_message = error_msg
            log.save()
            
            return {"status": "ERROR", "message": error_msg}
                
        except HTTPError as e:
            # HTTP error like network error, not found, etc.
            error_msg = f"HTTP error: {e}"
            logger.error(error_msg)
            print(error_msg)
            
            log.status = 'FAILED'
            log.error_message = error_msg
            log.save()
            
            return {"status": "ERROR", "message": error_msg}
                
        except json.JSONDecodeError as e:
            # JSON parsing error - likely empty or invalid response
            error_msg = f"Invalid JSON response from API: {e}"
            logger.error(error_msg)
            print(error_msg)
            
            log.status = 'FAILED'
            log.error_message = error_msg
            log.save()
            
            return {"status": "ERROR", "message": "Invalid response from SMS service. Please check your API configuration."}
            
        except Exception as e:
            # Unexpected error
            error_msg = f"Unexpected error: {e}"
            logger.error(error_msg)
            print(error_msg)
            
            log.status = 'FAILED'
            log.error_message = error_msg
            log.save()
            
            return {"status": "ERROR", "message": error_msg}

    @classmethod
    def send_bulk_sms(cls, recipient_numbers, message, sender_user=None, template=None):
        """
        Send SMS to multiple recipients
        
        Args:
            recipient_numbers: List of phone numbers
            message: The message content
            sender_user: The user sending the message (optional)
            template: The template used for the message (optional)
            
        Returns:
            dict: Response with status and details
        """
        successful_sends = []
        failed_sends = []
        
        for number in recipient_numbers:
            result = cls.send_sms(number, message, sender_user, None, template)
            if result["status"] == "OK":
                successful_sends.append(number)
            else:
                failed_sends.append({"number": number, "error": result["message"]})
        
        return {
            "status": "OK" if len(successful_sends) > 0 else "ERROR",
            "successful": successful_sends,
            "failed": failed_sends,
            "total_sent": len(successful_sends),
            "total_failed": len(failed_sends)
        }

# Keep compatibility with existing code
FarazSMSSender = IPPanelSMSSender

def get_default_template(template_type):
    """Get the default template for a given type"""
    return SMSTemplate.objects.filter(type=template_type, is_default=True).first()

def format_project_outdated_message(project_name):
    """Format message for outdated project notification"""
    template = get_default_template('PROJECT_OUTDATED')
    if not template:
        return f"با سلام وعرض ادب خدمت همکار گرامی لطفا به بروزسانی وضعیت پروژه {project_name} اقدام فرمایید"
    
    return template.content.replace('{name of project}', project_name)

def format_project_rejected_message(rejection_reason):
    """Format message for project rejection notification"""
    template = get_default_template('PROJECT_REJECTED')
    if not template:
        return f"با سلام وعرض ادب خدمت همکار گرامی به دلیل زیر پروژه نیازمند اصلاح است {rejection_reason}"
    
    return template.content.replace('{reason of rejection}', rejection_reason)

def format_project_not_examined_message(project_name):
    """Format message for project not examined notification"""
    template = get_default_template('PROJECT_NOT_EXAMINED')
    if not template:
        return f"با سلام وعرض ادب خدمت همکار گرامی لطفا به وضعیت پروژه {project_name} اقدام فرمایید"
    
    return template.content.replace('{name of project}', project_name)

def format_financing_approved_message(project_name, amount=None):
    """Format message for financing approved notification"""
    template = get_default_template('FINANCING_APPROVED')
    if not template:
        if amount:
            return f"با سلام وعرض ادب خدمت همکار گرامی تامین مالی پروژه {project_name} به مبلغ {amount} تأیید شد"
        return f"با سلام وعرض ادب خدمت همکار گرامی تامین مالی پروژه {project_name} تأیید شد"
    
    content = template.content.replace('{name of project}', project_name)
    if amount:
        content = content.replace('{amount}', str(amount))
    return content 