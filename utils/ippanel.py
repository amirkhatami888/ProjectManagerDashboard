import requests
import logging

logger = logging.getLogger(__name__)

class IPPanelClient:
    BASE_URL = 'https://edge.ippanel.com/v1'
    
    def __init__(self, api_key=None):
        self.api_key = api_key
        
    def send_sms(self, recipient_numbers, message_text, sender_number=None):
        """
        Send SMS to one or multiple recipients
        
        Args:
            recipient_numbers: Single number or list of phone numbers
            message_text: SMS content
            sender_number: Sender number (optional)
            
        Returns:
            Response from API or error dict
        """
        try:
            if isinstance(recipient_numbers, str):
                recipient_numbers = [recipient_numbers]
                
            # Make sure all numbers are strings and have correct format
            recipient_numbers = [str(num) for num in recipient_numbers]
            
            headers = {
                'Authorization': self.api_key,
                'Content-Type': 'application/json'
            }
            
            payload = {
                "message_text": message_text,
                "mobile": recipient_numbers
            }
            
            if sender_number:
                payload["sender"] = sender_number
                
            response = requests.post(
                f"{self.BASE_URL}/api/acl/message/sms/send", 
                json=payload, 
                headers=headers
            )
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error sending SMS: {str(e)}")
            return {"error": str(e), "status": False}
            
    def get_status(self, message_id):
        """
        Check the delivery status of a message
        
        Args:
            message_id: ID of the message to check
            
        Returns:
            Status response from API
        """
        try:
            headers = {
                'Authorization': self.api_key,
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.BASE_URL}/api/report/message/{message_id}", 
                headers=headers
            )
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error checking message status: {str(e)}")
            return {"error": str(e), "status": False} 