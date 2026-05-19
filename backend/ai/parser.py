import json
import re
import os
from typing import Dict, List, Optional
from pydantic import BaseModel, ValidationError
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class ParsedTransaction(BaseModel):
    amount: float
    merchant: str
    category: str
    confidence: float
    is_indulgence: bool

class TransactionParser:
    def __init__(self, api_key: str = None):
        """
        Initialize parser with free AI providers
        Supports: Google Gemini, Groq, GitHub Models, Cohere
        """
        self.provider = os.getenv("AI_PROVIDER", "google").lower()
        
        # Initialize the appropriate client based on provider
        if self.provider == "google":
            try:
                import google.generativeai as genai
                api_key = api_key or os.getenv("GOOGLE_API_KEY")
                if not api_key:
                    raise ValueError("GOOGLE_API_KEY not found in .env")
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("✅ Google Gemini initialized")
            except ImportError:
                raise ImportError("Install google-generativeai: pip install google-generativeai")
                
        elif self.provider == "groq":
            try:
                from openai import OpenAI
                api_key = api_key or os.getenv("GROQ_API_KEY")
                if not api_key:
                    raise ValueError("GROQ_API_KEY not found in .env")
                self.client = OpenAI(
                    base_url="https://api.groq.com/openai/v1",
                    api_key=api_key
                )
                self.model_name = "llama-3.3-70b-versatile"
                logger.info("✅ Groq initialized")
            except ImportError:
                raise ImportError("Install openai: pip install openai")
                
        elif self.provider == "github":
            try:
                from openai import OpenAI
                api_key = api_key or os.getenv("GITHUB_TOKEN")
                if not api_key:
                    raise ValueError("GITHUB_TOKEN not found in .env")
                self.client = OpenAI(
                    base_url="https://models.inference.ai.azure.com",
                    api_key=api_key
                )
                self.model_name = "gpt-4.1-mini"  # Free on GitHub
                logger.info("✅ GitHub Models initialized")
            except ImportError:
                raise ImportError("Install openai: pip install openai")
                
        elif self.provider == "cohere":
            try:
                import cohere
                api_key = api_key or os.getenv("COHERE_API_KEY")
                if not api_key:
                    raise ValueError("COHERE_API_KEY not found in .env")
                self.client = cohere.Client(api_key)
                logger.info("✅ Cohere initialized")
            except ImportError:
                raise ImportError("Install cohere: pip install cohere")
        else:
            raise ValueError(f"Unknown provider: {self.provider}. Use: google, groq, github, cohere")
    
    def parse_raw_text(self, raw_input: str, user_categories: List[str]) -> ParsedTransaction:
        """
        Parse messy transaction text into structured data using free AI providers
        """
        if not raw_input or not raw_input.strip():
            raise ValueError("Raw text cannot be empty")
        
        # Extract amount using regex (fallback)
        amount_match = re.search(r'(\d+(?:\.\d{2})?)', raw_input)
        amount = float(amount_match.group(1)) if amount_match else 0.0
        
        if amount == 0.0:
            raise ValueError("Could not extract amount from text")
        
        # Build prompt for all providers
        prompt = f"""Parse this transaction text and return ONLY valid JSON.
Do not include any other text, explanations, or markdown formatting.

Transaction text: "{raw_input}"
Available categories: {', '.join(user_categories)}

Return JSON with exactly this structure:
{{
    "amount": {amount},
    "merchant": "cleaned merchant name",
    "category": "best match from categories",
    "is_indulgence": true,
    "confidence": 0.95
}}

Rules:
- Use the amount: {amount}
- Clean merchant name (remove IDs, codes)
- Mark as indulgence unless it's rent/bills/groceries/essentials
- Confidence between 0.8-1.0"""

        try:
            result_text = self._call_ai_api(prompt)
            result = json.loads(result_text)
            
            # Validate and create ParsedTransaction
            parsed = ParsedTransaction(
                amount=float(result.get('amount', amount)),
                merchant=str(result.get('merchant', 'Unknown Merchant'))[:50],
                category=str(result.get('category', user_categories[0] if user_categories else 'Other')),
                confidence=float(result.get('confidence', 0.8)),
                is_indulgence=bool(result.get('is_indulgence', True))
            )
            
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}, response: {result_text if 'result_text' in locals() else 'No response'}")
            # Fallback with extracted amount
            return ParsedTransaction(
                amount=amount,
                merchant="Unknown Merchant",
                category=user_categories[0] if user_categories else 'Other',
                confidence=0.5,
                is_indulgence=True
            )
        except Exception as e:
            logger.error(f"AI parsing error: {e}")
            # Fallback to regex-only parsing
            return self._fallback_parse(raw_input, amount, user_categories)
    
    def _call_ai_api(self, prompt: str) -> str:
        """Call the selected AI provider's API"""
        
        if self.provider == "google":
            # Google Gemini
            response = self.model.generate_content(prompt)
            result = response.text.strip()
            # Clean markdown if present
            if result.startswith('```json'):
                result = result.replace('```json', '').replace('```', '')
            elif result.startswith('```'):
                result = result.replace('```', '')
            return result
            
        elif self.provider in ["groq", "github"]:
            # Groq or GitHub Models (both use OpenAI-compatible API)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a precise financial data extractor. Return ONLY valid JSON. No explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            result = response.choices[0].message.content.strip()
            # Clean markdown
            if result.startswith('```json'):
                result = result.replace('```json', '').replace('```', '')
            elif result.startswith('```'):
                result = result.replace('```', '')
            return result
            
        elif self.provider == "cohere":
            # Cohere
            response = self.client.generate(
                model='command-r',
                prompt=prompt,
                max_tokens=200,
                temperature=0.1
            )
            result = response.generations[0].text.strip()
            if result.startswith('```json'):
                result = result.replace('```json', '').replace('```', '')
            return result
            
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def _fallback_parse(self, raw_input: str, amount: float, user_categories: List[str]) -> ParsedTransaction:
        """Fallback parsing using regex when AI fails"""
        
        # Extract merchant using simple patterns
        merchant = "Unknown Merchant"
        
        # Try to extract merchant name
        patterns = [
            r'at\s+([A-Za-z\s]+?)(?:\s+for|\s+\(|$)',
            r'from\s+([A-Za-z\s]+?)(?:\s+\(|$)',
            r'^([A-Za-z\s]+?)(?:\s+-\s+|\s+\(|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, raw_input, re.IGNORECASE)
            if match:
                merchant = match.group(1).strip().title()
                if len(merchant) > 2:
                    break
        
        # Determine category based on keywords
        category = user_categories[0] if user_categories else 'Other'
        text_lower = raw_input.lower()
        
        category_keywords = {
            'Matcha/Tea': ['matcha', 'tea', 'tealive', 'chatime', 'bubble tea'],
            'Mamak': ['mamak', 'roti canai', 'teh tarik', 'nasi kandar'],
            'Fried Chicken': ['kfc', 'fried chicken', 'texas chicken', 'popeyes'],
            'Coffee': ['coffee', 'starbucks', 'latte', 'cappuccino', 'cafe'],
            'Groceries': ['groceries', 'supermarket', 'aeon', 'lotus', 'tesco'],
            'Essentials': ['rent', 'utility', 'bill', 'electricity', 'water']
        }
        
        for cat, keywords in category_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                if cat in user_categories:
                    category = cat
                    break
        
        is_indulgence = category not in ['Groceries', 'Essentials']
        
        return ParsedTransaction(
            amount=amount,
            merchant=merchant,
            category=category,
            confidence=0.6,
            is_indulgence=is_indulgence
        )
    
    def batch_parse(self, raw_texts: List[str], user_categories: List[str]) -> List[ParsedTransaction]:
        """Parse multiple transactions efficiently"""
        results = []
        for text in raw_texts:
            try:
                results.append(self.parse_raw_text(text, user_categories))
            except Exception as e:
                logger.error(f"Failed to parse '{text}': {e}")
                # Extract amount for fallback
                amount_match = re.search(r'(\d+(?:\.\d{2})?)', text)
                amount = float(amount_match.group(1)) if amount_match else 0.0
                results.append(ParsedTransaction(
                    amount=amount,
                    merchant="Parse Error",
                    category=user_categories[0] if user_categories else 'Other',
                    confidence=0.0,
                    is_indulgence=True
                ))
        return results