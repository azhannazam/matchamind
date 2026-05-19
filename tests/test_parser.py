import pytest
import sys
import os
import json
from unittest.mock import Mock, patch, MagicMock

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from ai.parser import TransactionParser, ParsedTransaction

class TestTransactionParser:
    """Test AI transaction parser with free providers"""
    
    @pytest.fixture
    def parser(self):
        """Create parser instance with mock configuration"""
        # Set environment for testing
        os.environ["AI_PROVIDER"] = "google"
        os.environ["GOOGLE_API_KEY"] = "test-key"
        
        with patch('ai.parser.genai') as mock_genai:
            mock_model = Mock()
            mock_genai.GenerativeModel.return_value = mock_model
            parser = TransactionParser(api_key="test-key")
            parser.provider = "google"  # Force google for testing
            parser.model = mock_model
            return parser
    
    @pytest.fixture
    def groq_parser(self):
        """Create parser for Groq testing"""
        os.environ["AI_PROVIDER"] = "groq"
        os.environ["GROQ_API_KEY"] = "test-key"
        
        with patch('ai.parser.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            parser = TransactionParser(api_key="test-key")
            parser.provider = "groq"
            parser.client = mock_client
            parser.model_name = "llama-3.3-70b-versatile"
            return parser
    
    def test_parse_matcha_transaction_google(self, parser):
        """Test parsing matcha transaction with Google Gemini"""
        # Mock Google Gemini response
        mock_response = Mock()
        mock_response.text = json.dumps({
            "amount": 45.90,
            "merchant": "Tealive",
            "category": "Matcha/Tea",
            "is_indulgence": True,
            "confidence": 0.95
        })
        parser.model.generate_content.return_value = mock_response
        
        result = parser.parse_raw_text(
            "RM 45.90 - Tealive (Matcha Latte)",
            ["Matcha/Tea", "Coffee", "Mamak"]
        )
        
        assert isinstance(result, ParsedTransaction)
        assert result.amount == 45.90
        assert result.merchant == "Tealive"
        assert result.category == "Matcha/Tea"
        assert result.is_indulgence == True
        assert result.confidence > 0
    
    def test_parse_mamak_transaction_groq(self, groq_parser):
        """Test parsing mamak transaction with Groq"""
        # Mock Groq response
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = json.dumps({
            "amount": 18.50,
            "merchant": "Nasi Kandar Pelita",
            "category": "Mamak",
            "is_indulgence": True,
            "confidence": 0.92
        })
        mock_response.choices = [mock_choice]
        groq_parser.client.chat.completions.create.return_value = mock_response
        
        result = groq_parser.parse_raw_text(
            "Nasi Kandar Pelita - RM 18.50",
            ["Matcha/Tea", "Coffee", "Mamak"]
        )
        
        assert result.amount == 18.50
        assert result.merchant == "Nasi Kandar Pelita"
        assert result.category == "Mamak"
    
    def test_parse_grocery_transaction(self, parser):
        """Test parsing grocery transaction (non-indulgence)"""
        mock_response = Mock()
        mock_response.text = json.dumps({
            "amount": 120.50,
            "merchant": "AEON Big",
            "category": "Groceries",
            "is_indulgence": False,
            "confidence": 0.98
        })
        parser.model.generate_content.return_value = mock_response
        
        result = parser.parse_raw_text(
            "RM 120.50 - AEON Big groceries",
            ["Groceries", "Essentials", "Matcha/Tea"]
        )
        
        assert result.is_indulgence == False
        assert result.category == "Groceries"
    
    def test_parse_empty_text(self, parser):
        """Test parsing empty text raises error"""
        with pytest.raises(ValueError):
            parser.parse_raw_text("", ["Test"])
    
    def test_parse_no_amount(self, parser):
        """Test parsing text with no amount"""
        with pytest.raises(ValueError):
            parser.parse_raw_text("No numbers here", ["Test"])
    
    def test_parse_with_fallback_regex(self, parser):
        """Test parser falls back to regex extraction when AI fails"""
        # Mock API failure
        parser.model.generate_content.side_effect = Exception("API Error")
        
        # Should fall back to regex extraction
        result = parser.parse_raw_text(
            "RM 25.90 at Starbucks",
            ["Coffee", "Matcha/Tea"]
        )
        
        assert result.amount == 25.90
        assert result.merchant == "Starbucks"  # Regex should extract this
        assert result.confidence == 0.6  # Fallback confidence
    
    def test_fallback_merchant_extraction(self, parser):
        """Test fallback merchant extraction patterns"""
        # Force fallback by making AI fail
        parser.model.generate_content.side_effect = Exception("API Error")
        
        test_cases = [
            ("RM 45.90 at Tealive", "Tealive"),
            ("KFC: RM 32.40", "Kfc"),
            ("From Starbucks - RM 18.50", "Starbucks"),
        ]
        
        for text, expected_merchant in test_cases:
            result = parser.parse_raw_text(text, ["Coffee", "Matcha/Tea"])
            assert expected_merchant.lower() in result.merchant.lower()
    
    def test_fallback_category_detection(self, parser):
        """Test fallback category detection based on keywords"""
        parser.model.generate_content.side_effect = Exception("API Error")
        
        test_cases = [
            ("Matcha latte from Tealive", "Matcha/Tea"),
            ("KFC fried chicken", "Fried Chicken"),
            ("Nasi Kandar mamak", "Mamak"),
            ("Starbucks coffee", "Coffee"),
            ("AEON grocery shopping", "Groceries"),
        ]
        
        categories = ["Matcha/Tea", "Fried Chicken", "Mamak", "Coffee", "Groceries"]
        
        for text, expected_category in test_cases:
            result = parser.parse_raw_text(text, categories)
            assert result.category == expected_category
    
    def test_batch_parse(self, parser):
        """Test batch parsing multiple transactions"""
        texts = [
            "RM 45.90 - Tealive",
            "KFC: RM 32.40",
            "RM 18.50 - Mamak"
        ]
        
        # Mock individual parses
        with patch.object(parser, 'parse_raw_text') as mock_parse:
            mock_parse.side_effect = [
                ParsedTransaction(amount=45.90, merchant="Tealive", category="Matcha/Tea", confidence=0.9, is_indulgence=True),
                ParsedTransaction(amount=32.40, merchant="KFC", category="Fried Chicken", confidence=0.9, is_indulgence=True),
                ParsedTransaction(amount=18.50, merchant="Mamak", category="Mamak", confidence=0.9, is_indulgence=True)
            ]
            
            results = parser.batch_parse(texts, ["Matcha/Tea", "Fried Chicken", "Mamak"])
            
            assert len(results) == 3
            assert all(isinstance(r, ParsedTransaction) for r in results)
    
    def test_batch_parse_with_failures(self, parser):
        """Test batch parsing handles failures gracefully"""
        texts = [
            "RM 45.90 - Tealive",
            "Invalid text with no numbers",
            "RM 18.50 - Mamak"
        ]
        
        # Mock parse to fail on second item
        with patch.object(parser, 'parse_raw_text') as mock_parse:
            mock_parse.side_effect = [
                ParsedTransaction(amount=45.90, merchant="Tealive", category="Matcha/Tea", confidence=0.9, is_indulgence=True),
                ValueError("No amount found"),
                ParsedTransaction(amount=18.50, merchant="Mamak", category="Mamak", confidence=0.9, is_indulgence=True)
            ]
            
            results = parser.batch_parse(texts, ["Matcha/Tea", "Mamak"])
            
            assert len(results) == 3
            # Third result should be the fallback
            assert results[1].merchant == "Parse Error"
            assert results[1].confidence == 0.0

class TestProviderInitialization:
    """Test different provider initializations"""
    
    @patch('ai.parser.genai')
    def test_google_provider_init(self, mock_genai):
        """Test Google Gemini provider initialization"""
        os.environ["AI_PROVIDER"] = "google"
        os.environ["GOOGLE_API_KEY"] = "test-key"
        
        parser = TransactionParser(api_key="test-key")
        assert parser.provider == "google"
    
    @patch('ai.parser.OpenAI')
    def test_groq_provider_init(self, mock_openai):
        """Test Groq provider initialization"""
        os.environ["AI_PROVIDER"] = "groq"
        os.environ["GROQ_API_KEY"] = "test-key"
        
        parser = TransactionParser(api_key="test-key")
        assert parser.provider == "groq"
    
    @patch('ai.parser.OpenAI')
    def test_github_provider_init(self, mock_openai):
        """Test GitHub Models provider initialization"""
        os.environ["AI_PROVIDER"] = "github"
        os.environ["GITHUB_TOKEN"] = "test-token"
        
        parser = TransactionParser(api_key="test-token")
        assert parser.provider == "github"
    
    def test_invalid_provider(self):
        """Test invalid provider raises error"""
        os.environ["AI_PROVIDER"] = "invalid"
        
        with pytest.raises(ValueError):
            TransactionParser()

class TestAmountExtraction:
    """Test amount extraction from various formats"""
    
    def test_extract_rm_format(self):
        """Test RM currency format"""
        import re
        text = "RM 45.90 at Tealive"
        match = re.search(r'(\d+(?:\.\d{2})?)', text)
        assert match.group(1) == "45.90"
    
    def test_extract_myr_format(self):
        """Test MYR currency format"""
        text = "MYR 32.50 for lunch"
        match = re.search(r'(\d+(?:\.\d{2})?)', text)
        assert match.group(1) == "32.50"
    
    def test_extract_no_currency(self):
        """Test amount without currency symbol"""
        text = "Paid 129 for matcha powder"
        match = re.search(r'(\d+(?:\.\d{2})?)', text)
        assert match.group(1) == "129"
    
    def test_extract_decimal_amount(self):
        """Test decimal amounts"""
        text = "RM 18.50 at mamak"
        match = re.search(r'(\d+(?:\.\d{2})?)', text)
        assert match.group(1) == "18.50"
    
    def test_extract_multiple_numbers_takes_first(self):
        """Test text with multiple numbers (should take first)"""
        text = "Order #12345 - RM 45.90 for 2 drinks"
        match = re.search(r'(\d+(?:\.\d{2})?)', text)
        # Note: This extracts the first number (12345), which might not be ideal
        # But our parser has additional logic to handle this
        assert match.group(1) == "12345"
    
    def test_extract_amount_with_commas(self):
        """Test amounts with thousand separators"""
        text = "RM 1,234.56 for laptop"
        # Clean commas first
        cleaned = re.sub(r',', '', text)
        match = re.search(r'(\d+(?:\.\d{2})?)', cleaned)
        assert match.group(1) == "1234.56"

class TestEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.fixture
    def parser(self):
        os.environ["AI_PROVIDER"] = "google"
        os.environ["GOOGLE_API_KEY"] = "test-key"
        with patch('ai.parser.genai') as mock_genai:
            mock_model = Mock()
            mock_genai.GenerativeModel.return_value = mock_model
            return TransactionParser(api_key="test-key")
    
    def test_unicode_characters(self, parser):
        """Test parsing text with unicode characters"""
        parser.model.generate_content.side_effect = Exception("API Error")
        
        result = parser.parse_raw_text(
            "🍵 Matcha Latte RM 25.90 at Tealive 😋",
            ["Matcha/Tea", "Coffee"]
        )
        
        assert result.amount == 25.90
        assert "Tealive" in result.merchant or result.merchant == "Unknown Merchant"
    
    def test_very_long_text(self, parser):
        """Test parsing very long text"""
        long_text = "RM 45.90 " + "Tealive " * 100
        parser.model.generate_content.side_effect = Exception("API Error")
        
        result = parser.parse_raw_text(long_text, ["Matcha/Tea"])
        
        assert result.amount == 45.90
    
    def test_special_characters_in_merchant(self, parser):
        """Test merchant names with special characters"""
        parser.model.generate_content.side_effect = Exception("API Error")
        
        result = parser.parse_raw_text(
            "RM 32.50 at McDonald's/KFC",
            ["Fast Food"]
        )
        
        assert result.amount == 32.50
    
    def test_lowercase_text(self, parser):
        """Test lowercase text parsing"""
        parser.model.generate_content.side_effect = Exception("API Error")
        
        result = parser.parse_raw_text(
            "rm 45.90 at tealive matcha latte",
            ["Matcha/Tea"]
        )
        
        assert result.amount == 45.90
        assert "tealive" in result.merchant.lower() or result.merchant == "Unknown Merchant"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])