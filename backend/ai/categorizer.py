from openai import OpenAI
from typing import List, Dict
import json

class SmartCategorizer:
    """Intelligent transaction categorizer that learns from user behavior"""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.category_history = {}  # In production, store in Redis/DB
    
    def categorize_transaction(self, merchant: str, amount: float, 
                               available_categories: List[str], 
                               previous_merchants: Dict[str, str] = None) -> Dict:
        """
        Categorize a transaction based on merchant name and amount
        """
        
        # Check if we've seen this merchant before
        if previous_merchants and merchant in previous_merchants:
            return {
                "category": previous_merchants[merchant],
                "confidence": 0.9,
                "method": "history"
            }
        
        prompt = f"""
        You are a smart expense categorizer. Categorize this transaction:
        
        Merchant: {merchant}
        Amount: RM {amount:.2f}
        
        Available categories: {', '.join(available_categories)}
        
        Rules:
        - Matcha/Tea: tea shops, bubble tea, matcha specialty stores
        - Mamak: Indian-Muslim food stalls, roti canai, teh tarik
        - Fried Chicken: KFC, Texas, Popeyes, any fried chicken chains
        - Coffee: Starbucks, Zus, Coffee Bean, specialty coffee
        - Groceries: supermarkets, wet markets, grocery delivery
        - Essentials: bills, utilities, transport, healthcare
        - Dining Out: restaurants, cafes, food courts (non-specialty)
        
        Return JSON:
        {{
            "category": "best match from list",
            "confidence": 0.0-1.0,
            "reasoning": "brief explanation"
        }}
        """
        
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
    
    def batch_categorize(self, transactions: List[Dict], categories: List[str]) -> List[Dict]:
        """Categorize multiple transactions efficiently"""
        categorized = []
        
        for transaction in transactions:
            result = self.categorize_transaction(
                transaction['merchant'],
                transaction['amount'],
                categories,
                None
            )
            categorized.append({
                **transaction,
                'suggested_category': result['category'],
                'confidence': result['confidence']
            })
        
        return categorized
    
    def suggest_new_category(self, transactions: List[Dict], existing_categories: List[str]) -> List[str]:
        """Suggest new categories based on uncategorized spending patterns"""
        
        # Group similar merchants
        merchants = list(set([t['merchant'] for t in transactions if not t.get('category_id')]))
        
        if len(merchants) < 3:
            return []
        
        prompt = f"""
        Analyze these merchants that don't fit existing categories:
        {', '.join(merchants[:10])}
        
        Existing categories: {', '.join(existing_categories)}
        
        Suggest 1-3 new categories that would group these merchants logically.
        Each category should have at least 2 potential merchants.
        
        Return JSON:
        {{
            "suggestions": [
                {{
                    "name": "Category Name",
                    "merchants": ["merchant1", "merchant2"],
                    "reasoning": "why this makes sense"
                }}
            ]
        }}
        """
        
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get('suggestions', [])
    
    def detect_misclassified(self, transaction_history: List[Dict]) -> List[Dict]:
        """Detect potentially misclassified transactions using AI"""
        
        # Find transactions that seem out of place for their category
        anomalies = []
        
        # Group by category
        by_category = {}
        for t in transaction_history:
            cat = t.get('category_name')
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(t)
        
        for category, transactions in by_category.items():
            if len(transactions) < 5:
                continue
                
            # Calculate average amount for category
            avg_amount = sum(t['amount'] for t in transactions) / len(transactions)
            std_amount = (sum((t['amount'] - avg_amount) ** 2 for t in transactions) / len(transactions)) ** 0.5
            
            # Find outliers
            for t in transactions:
                if abs(t['amount'] - avg_amount) > 2 * std_amount:
                    anomalies.append({
                        'transaction_id': t.get('id'),
                        'merchant': t['merchant'],
                        'amount': t['amount'],
                        'current_category': category,
                        'reason': f"Amount (RM{t['amount']:.2f}) is unusual for {category}",
                        'suggested_action': 'review'
                    })
        
        return anomalies