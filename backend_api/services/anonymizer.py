"""
Anonymizer Service for Knowledge-Weaver
HIPAA-compliant data anonymization before sending to external APIs
"""
import re
import logging

logger = logging.getLogger(__name__)


class AnonymizerService:
    """
    Service for anonymizing sensitive data in chat logs
    This is a placeholder implementation for hackathon purposes
    Production systems should use more sophisticated anonymization
    """
    
    def __init__(self):
        # Compile regex patterns for better performance
        self.patterns = {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b'),
            'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            'participant_id': re.compile(r'(?:participant|patient|member).*?ID[:\s]+(\w{5,})', re.IGNORECASE),
            'employee_id': re.compile(r'(?:employee|emp|staff).*?ID[:\s]+(\w{5,})', re.IGNORECASE),
            'generic_id': re.compile(r'\bID[:\s]+([A-Z0-9]{5,})\b', re.IGNORECASE),
            'agent_handle': re.compile(r'\b(Agent|Representative|Support)_([A-Za-z0-9]+)\b', re.IGNORECASE),
            'lead_handle': re.compile(r'\b(Lead|Supervisor|Manager)_([A-Za-z0-9]+)\b', re.IGNORECASE),
        }
        
        logger.info("AnonymizerService initialized")
    
    def anonymize_text(self, text: str) -> str:
        """
        Anonymize sensitive information in text
        
        Args:
            text: Raw text containing potentially sensitive information
        
        Returns:
            Anonymized text with sensitive data replaced
        """
        if not text:
            return text
        
        anonymized = text
        replacements_made = 0
        
        # Replace email addresses
        email_matches = self.patterns['email'].findall(anonymized)
        if email_matches:
            anonymized = self.patterns['email'].sub('[EMAIL_REDACTED]', anonymized)
            replacements_made += len(email_matches)
            logger.debug(f"Anonymized {len(email_matches)} email addresses")
        
        # Replace phone numbers
        phone_matches = self.patterns['phone'].findall(anonymized)
        if phone_matches:
            anonymized = self.patterns['phone'].sub('[PHONE_REDACTED]', anonymized)
            replacements_made += len(phone_matches)
            logger.debug(f"Anonymized {len(phone_matches)} phone numbers")
        
        # Replace SSNs
        ssn_matches = self.patterns['ssn'].findall(anonymized)
        if ssn_matches:
            anonymized = self.patterns['ssn'].sub('[SSN_REDACTED]', anonymized)
            replacements_made += len(ssn_matches)
            logger.debug(f"Anonymized {len(ssn_matches)} SSNs")
        
        # Replace participant IDs
        participant_matches = self.patterns['participant_id'].findall(anonymized)
        if participant_matches:
            anonymized = self.patterns['participant_id'].sub(r'\1 [PARTICIPANT_ID_REDACTED]', anonymized)
            replacements_made += len(participant_matches)
            logger.debug(f"Anonymized {len(participant_matches)} participant IDs")
        
        # Replace employee IDs
        employee_matches = self.patterns['employee_id'].findall(anonymized)
        if employee_matches:
            anonymized = self.patterns['employee_id'].sub(r' [EMPLOYEE_ID_REDACTED]', anonymized)
            replacements_made += len(employee_matches)
            logger.debug(f"Anonymized {len(employee_matches)} employee IDs")

        # Replace Generic IDs (fallback)
        generic_matches = self.patterns['generic_id'].findall(anonymized)
        if generic_matches:
            anonymized = self.patterns['generic_id'].sub('[ID_REDACTED]', anonymized)
            replacements_made += len(generic_matches)
            logger.debug(f"Anonymized {len(generic_matches)} generic IDs")

        # Replace Agent Handles
        agent_matches = self.patterns['agent_handle'].findall(anonymized)
        if agent_matches:
            anonymized = self.patterns['agent_handle'].sub('Questioner', anonymized)
            replacements_made += len(agent_matches)
            logger.debug(f"Anonymized {len(agent_matches)} agent handles")

        # Replace Lead Handles
        lead_matches = self.patterns['lead_handle'].findall(anonymized)
        if lead_matches:
            anonymized = self.patterns['lead_handle'].sub('Respondent', anonymized)
            replacements_made += len(lead_matches)
            logger.debug(f"Anonymized {len(lead_matches)} lead handles")
        
        if replacements_made > 0:
            logger.info(f"Anonymized {replacements_made} sensitive data items")
        
        return anonymized
    
    def anonymize_batch(self, texts: list) -> list:
        """
        Anonymize a batch of texts
        
        Args:
            texts: List of text strings to anonymize
        
        Returns:
            List of anonymized texts
        """
        return [self.anonymize_text(text) for text in texts]
