"""
Gemini API Client for Knowledge-Weaver
Handles interactions with Google's Gemini API for knowledge extraction and embeddings
"""
import os
import time
import logging
from typing import List, Dict, Any
import google.generativeai as genai

from models.schemas import ChatMessage, KnowledgeEntry

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for interacting with Google Gemini API"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize Gemini API client
        
        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env variable)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=self.api_key)
        
        # Initialize models
        # Using specific version widely supported, configurable via env
        generation_model_name = os.getenv('GEMINI_GENERATION_MODEL', 'gemini-2.0-flash')
        embedding_model_name = os.getenv('GEMINI_EMBEDDING_MODEL', 'models/text-embedding-004')
        
        self.generation_model = genai.GenerativeModel(generation_model_name)
        self.embedding_model = embedding_model_name
        
        logger.info(f"GeminiClient initialized with models: Gen={generation_model_name}, Embed={embedding_model_name}")
    
    def extract_knowledge(
        self,
        messages: List[ChatMessage],
        max_retries: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Analyze chat messages and extract knowledge using Gemini API
        
        Args:
            messages: List of ChatMessage objects to analyze
            max_retries: Maximum number of retry attempts for transient failures
        
        Returns:
            List of extracted knowledge entries as dictionaries
        """
        if not messages:
            return []
        
        # Build prompt for knowledge extraction
        prompt = self._build_extraction_prompt(messages)
        
        # Retry logic for transient failures
        for attempt in range(max_retries):
            try:
                response = self.generation_model.generate_content(prompt)
                
                # Parse the response to extract knowledge
                knowledge_entries = self._parse_extraction_response(
                    response.text,
                    messages
                )
                
                logger.info(f"Extracted {len(knowledge_entries)} knowledge entries from {len(messages)} messages")
                return knowledge_entries
            
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                
                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to extract knowledge after {max_retries} attempts")
                    raise
        
        return []
    
    def generate_embedding(
        self,
        text: str,
        max_retries: int = 3
    ) -> List[float]:
        """
        Generate vector embedding for text using Gemini API
        
        Args:
            text: Text to generate embedding for
            max_retries: Maximum number of retry attempts
        
        Returns:
            768-dimensional embedding vector
        """
        if not text:
            raise ValueError("Text cannot be empty")
        
        # Retry logic for transient failures
        for attempt in range(max_retries):
            try:
                result = genai.embed_content(
                    model=self.embedding_model,
                    content=text,
                    task_type="retrieval_document"
                )
                
                embedding = result['embedding']
                logger.debug(f"Generated embedding of dimension {len(embedding)}")
                return embedding
            
            except Exception as e:
                logger.warning(f"Embedding attempt {attempt + 1}/{max_retries} failed: {e}")
                
                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to generate embedding after {max_retries} attempts")
                    raise
        
        return []
    
    def generate_query_embedding(
        self,
        query: str,
        max_retries: int = 3
    ) -> List[float]:
        """
        Generate vector embedding for a query using Gemini API
        
        Args:
            query: Query text to generate embedding for
            max_retries: Maximum number of retry attempts
        
        Returns:
            768-dimensional embedding vector
        """
        if not query:
            raise ValueError("Query cannot be empty")
        
        # Retry logic for transient failures
        for attempt in range(max_retries):
            try:
                result = genai.embed_content(
                    model=self.embedding_model,
                    content=query,
                    task_type="retrieval_query"
                )
                
                embedding = result['embedding']
                logger.debug(f"Generated query embedding of dimension {len(embedding)}")
                return embedding
            
            except Exception as e:
                logger.warning(f"Query embedding attempt {attempt + 1}/{max_retries} failed: {e}")
                
                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to generate query embedding after {max_retries} attempts")
                    raise
        
        return []
    
    def _build_extraction_prompt(self, messages: List[ChatMessage]) -> str:
        """
        Build prompt for knowledge extraction from chat messages
        
        Args:
            messages: List of chat messages
        
        Returns:
            Formatted prompt string
        """
        chat_text = "\n".join([
            f"[{msg.timestamp}] {msg.sender}: {msg.content}"
            for msg in messages
        ])
        
        prompt = f"""Analyze the following chat conversation and extract valuable knowledge that should be preserved.
Focus on:
1. Questions and their answers (Q&A pairs)
2. Policy statements or decisions
3. Important procedural information
4. Key decisions made

CRITICAL ANONYMIZATION RULE:
- Replace ALL real names with functional roles based on the conversation flow.
- If a user asks a question, refer to them as 'Questioner'.
- If a user provides policy/answers, refer to them as 'Authority' or 'Answerer'.
- Do NOT output real names in the content or participants list.

For each piece of knowledge found, provide:
- Type: "qa", "policy", or "decision"
- Content: The actual knowledge text (using ROLES, not names)
- Confidence: A score from 0.0 to 1.0 indicating how confident you are this is valuable knowledge

Format your response as a JSON array of objects with fields: type, content, confidence

Chat conversation:
{chat_text}

Extract knowledge:"""
        
        return prompt
    
    def _parse_extraction_response(
        self,
        response_text: str,
        source_messages: List[ChatMessage]
    ) -> List[Dict[str, Any]]:
        """
        Parse Gemini API response to extract knowledge entries
        
        Args:
            response_text: Raw response from Gemini API
            source_messages: Original chat messages
        
        Returns:
            List of knowledge entry dictionaries
        """
        import json
        import re
        
        knowledge_entries = []
        
        try:
            # Try to extract JSON from response
            # Look for JSON array in the response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                parsed_entries = json.loads(json_str)
                
                # Convert to knowledge entry format
                for entry in parsed_entries:
                    if isinstance(entry, dict) and 'content' in entry:
                        knowledge_entries.append({
                            'entry_type': entry.get('type', 'qa'),
                            'content': entry.get('content', ''),
                            'confidence_score': float(entry.get('confidence', 0.7)),
                            'source_message_ids': [msg.id for msg in source_messages],
                            'participants': list(set(msg.sender for msg in source_messages))
                        })
            else:
                logger.warning("No JSON found in response, treating entire response as single knowledge entry")
                # Fallback: treat entire response as single knowledge entry
                if response_text.strip():
                    knowledge_entries.append({
                        'entry_type': 'qa',
                        'content': response_text.strip(),
                        'confidence_score': 0.6,
                        'source_message_ids': [msg.id for msg in source_messages],
                        'participants': list(set(msg.sender for msg in source_messages))
                    })
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            # Fallback: treat response as single entry
            if response_text.strip():
                knowledge_entries.append({
                    'entry_type': 'qa',
                    'content': response_text.strip(),
                    'confidence_score': 0.5,
                    'source_message_ids': [msg.id for msg in source_messages],
                    'participants': list(set(msg.sender for msg in source_messages))
                })
        
        return knowledge_entries


    def process_messages_in_batches(
        self,
        messages: List[ChatMessage],
        batch_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Process chat messages in batches to respect API limits
        
        Args:
            messages: List of all chat messages to process
            batch_size: Maximum messages per batch (default: 100)
        
        Returns:
            Combined list of all extracted knowledge entries
        """
        if not messages:
            return []
        
        all_knowledge = []
        total_batches = (len(messages) + batch_size - 1) // batch_size
        
        logger.info(f"Processing {len(messages)} messages in {total_batches} batches")
        
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} messages)")
            
            try:
                batch_knowledge = self.extract_knowledge(batch)
                all_knowledge.extend(batch_knowledge)
            except Exception as e:
                logger.error(f"Failed to process batch {batch_num}: {e}")
                # Continue with next batch instead of failing completely
                continue
        
        logger.info(f"Total knowledge entries extracted: {len(all_knowledge)}")
        return all_knowledge
    def analyze_content(
        self,
        text: str,
        context_examples: str = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Analyze content to extract category, tags, and summary
        
        Args:
            text: Text content to analyze
            context_examples: Optional string containing similar verified examples
            max_retries: Maximum number of retry attempts
        
        Returns:
            Dictionary with category, tags, and summary
        """
        if not text:
            raise ValueError("Text cannot be empty")
            
        # Base prompt
        prompt = f"""Analyze the following text and provide:
1. A category (e.g., "Policy", "Procedure", "Q&A", "Announcement", "Policy / Enrollment Denied", "Compliance / Authorization")
2. A list of relevant tags (MINIMUM 2, max 5) - IMPORTANT: You MUST always provide at least 2 tags. If no specific tags are obvious, infer topic-based tags from the content (e.g., "general", "internal", "communication", "workflow", "documentation").
3. A concise summary (max 2 sentences)

CRITICAL TAG REQUIREMENTS:
- Never return an empty tags array
- Always provide at least 2 relevant tags
- Tags should describe the topic, domain, or subject matter
- If content is generic, use descriptive tags like: "general", "operations", "internal", "communication", "process"

Here are some examples of how to classify specific scenarios:

Example 1 (Policy Denial):
Input: "Agent: EE sent marriage certificate today, wedding was 45 days ago. Lead: Denied. QLE Policy requires docs within 31 days."
Output Category: "Policy / Enrollment Denied"
Output Tags: ["QLE", "marriage", "enrollment", "deadline", "policy"]

Example 2 (HIPAA Compliance):
Input: "Agent: Wife on line asking about husband's dental, he can't talk. Lead: Do not discuss unless she is Authorized Rep. Need EE permission."
Output Category: "Compliance / Authorization"
Output Tags: ["HIPAA", "authorization", "privacy", "dependent"]

Example 3 (Generic Content):
Input: "Team meeting notes from Monday standup."
Output Category: "Internal"
Output Tags: ["meeting", "internal", "operations"]
"""

        # Add dynamic examples if provided
        if context_examples:
            prompt += f"\nHere are past examples of how the user classified similar text:\n{context_examples}\n"
            prompt += "\nCRITICAL: You will be provided with 'Verified Examples' from the user's history. You MUST mimic the tagging style, category choice, and summary format of these examples exactly. They are your ground truth.\n"

        prompt += f"""
Text to Analyze:
{text}

Format your response as a JSON object with keys: "category", "tags", "summary".
REMINDER: The "tags" array MUST contain at least 2 items.
"""
        
        for attempt in range(max_retries):
            try:
                response = self.generation_model.generate_content(prompt)
                
                # Parse JSON response
                import json
                import re
                
                # Try to find JSON block
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    result = json.loads(json_str)
                    
                    # Ensure tags is never empty
                    tags = result.get("tags", [])
                    if not tags or len(tags) < 2:
                        # Fallback: infer basic tags from category
                        category = result.get("category", "General")
                        fallback_tags = [category.split("/")[0].strip().lower(), "captured"]
                        tags = list(set(tags + fallback_tags))[:5]
                    
                    # Validate structure
                    return {
                        "category": result.get("category", "Uncategorized"),
                        "tags": tags,
                        "summary": result.get("summary", "No summary available")
                    }
                
                # Fallback if no JSON found
                logger.warning("No JSON found in analysis response")
                return {
                    "category": "Uncategorized",
                    "tags": ["general", "captured"],
                    "summary": "Analysis failed to produce structured output"
                }
                
            except Exception as e:
                logger.warning(f"Analysis attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    logger.error("Failed to analyze content")
                    raise
        
        return {
            "category": "Uncategorized",
            "tags": [],
            "summary": "Analysis failed"
        }
