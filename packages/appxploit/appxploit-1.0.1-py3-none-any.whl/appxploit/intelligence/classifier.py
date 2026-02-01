"""
App Classification Module
Classifies apps by type and purpose based on fingerprint data
"""

from typing import Dict, Any


class AppClassifier:
    """Classify Android apps by type and purpose"""
    
    def __init__(self, fingerprint: Dict[str, Any], config):
        self.fingerprint = fingerprint
        self.config = config
    
    def classify(self) -> Dict[str, Any]:
        """
        Classify app based on package name, permissions, and libraries
        
        Returns:
            Classification data with app_type and risk_category
        """
        package_name = self.fingerprint.get('package_name', '').lower()
        libraries = [lib.lower() for lib in self.fingerprint.get('libraries', [])]
        
        result = {
            'app_type': 'unknown',
            'category': 'general',
            'risk_category': 'medium',
            'description': ''
        }
        
        # Fintech detection
        if self._is_fintech(package_name, libraries):
            result['app_type'] = 'fintech'
            result['category'] = 'financial'
            result['risk_category'] = 'critical'
            result['description'] = 'Financial application - high-value target'
        
        # Social media detection
        elif self._is_social(package_name, libraries):
            result['app_type'] = 'social'
            result['category'] = 'social_media'
            result['risk_category'] = 'high'
            result['description'] = 'Social media application - privacy concerns'
        
        # E-commerce detection
        elif self._is_ecommerce(package_name, libraries):
            result['app_type'] = 'ecommerce'
            result['category'] = 'shopping'
            result['risk_category'] = 'high'
            result['description'] = 'E-commerce application - payment data at risk'
        
        # Healthcare detection
        elif self._is_healthcare(package_name, libraries):
            result['app_type'] = 'healthcare'
            result['category'] = 'medical'
            result['risk_category'] = 'critical'
            result['description'] = 'Healthcare application - sensitive medical data'
        
        # Messaging detection
        elif self._is_messaging(package_name, libraries):
            result['app_type'] = 'messaging'
            result['category'] = 'communication'
            result['risk_category'] = 'high'
            result['description'] = 'Messaging application - private communications'
        
        # Gaming detection
        elif self._is_gaming(package_name, libraries):
            result['app_type'] = 'gaming'
            result['category'] = 'entertainment'
            result['risk_category'] = 'low'
            result['description'] = 'Gaming application - lower risk profile'
        
        # Utility detection
        elif self._is_utility(package_name, libraries):
            result['app_type'] = 'utility'
            result['category'] = 'tools'
            result['risk_category'] = 'medium'
            result['description'] = 'Utility application - standard risk'
        
        return result
    
    def _is_fintech(self, package: str, libraries: list) -> bool:
        """Detect fintech apps"""
        fintech_keywords = [
            'bank', 'banking', 'finance', 'payment', 'wallet', 'pay',
            'money', 'credit', 'debit', 'loan', 'invest', 'trading',
            'crypto', 'bitcoin', 'paypal', 'stripe', 'venmo'
        ]
        return any(keyword in package for keyword in fintech_keywords)
    
    def _is_social(self, package: str, libraries: list) -> bool:
        """Detect social media apps"""
        social_keywords = [
            'social', 'facebook', 'instagram', 'twitter', 'snapchat',
            'tiktok', 'linkedin', 'reddit', 'whatsapp', 'telegram'
        ]
        
        has_facebook_sdk = any('facebook' in lib for lib in libraries)
        
        return any(keyword in package for keyword in social_keywords) or has_facebook_sdk
    
    def _is_ecommerce(self, package: str, libraries: list) -> bool:
        """Detect e-commerce apps"""
        ecommerce_keywords = [
            'shop', 'store', 'market', 'buy', 'sell', 'commerce',
            'amazon', 'ebay', 'alibaba', 'cart', 'checkout'
        ]
        return any(keyword in package for keyword in ecommerce_keywords)
    
    def _is_healthcare(self, package: str, libraries: list) -> bool:
        """Detect healthcare apps"""
        healthcare_keywords = [
            'health', 'medical', 'doctor', 'hospital', 'clinic',
            'patient', 'medicine', 'pharmacy', 'fitness', 'wellness'
        ]
        return any(keyword in package for keyword in healthcare_keywords)
    
    def _is_messaging(self, package: str, libraries: list) -> bool:
        """Detect messaging apps"""
        messaging_keywords = [
            'message', 'chat', 'messenger', 'sms', 'mms',
            'signal', 'telegram', 'whatsapp', 'wechat'
        ]
        return any(keyword in package for keyword in messaging_keywords)
    
    def _is_gaming(self, package: str, libraries: list) -> bool:
        """Detect gaming apps"""
        gaming_keywords = [
            'game', 'play', 'gaming', 'arcade', 'puzzle',
            'racing', 'action', 'adventure', 'rpg'
        ]
        
        has_unity = any('unity' in lib for lib in libraries)
        is_game_package = package.startswith('com.game.') or '.game.' in package
        
        return any(keyword in package for keyword in gaming_keywords) or has_unity or is_game_package
    
    def _is_utility(self, package: str, libraries: list) -> bool:
        """Detect utility apps"""
        utility_keywords = [
            'util', 'tool', 'manager', 'cleaner', 'optimizer',
            'scanner', 'reader', 'viewer', 'editor'
        ]
        return any(keyword in package for keyword in utility_keywords)
