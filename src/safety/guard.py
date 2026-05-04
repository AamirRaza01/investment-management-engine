
class SafetyVerdict:
    def __init__(self, blocked: bool, category: str = None, message: str = None):
        self.blocked = blocked
        self.category = category
        self.message = message


class SafetyGuard:
    def __init__(self):
        self.blocked_patterns = {
            "insider_trading": [
                "insider", "non public", "confidential", "inside info", "leak"
            ],
            "market_manipulation": [
                "pump", "dump", "manipulate", "rig", "artificial price"
            ],
            "money_laundering": [
                "launder", "clean money", "hide money", "illegal funds"
            ],
            "guaranteed_returns": [
                "guaranteed", "100%", "sure profit", "risk free"
            ],
            "financial_fraud": [
                "scam", "fraud", "cheat", "fake investment"
            ],
            "illegal_advice": [
                "tax evasion", "avoid tax illegally", "hide income"
            ],
            "high_risk_behavior": [
                "all in", "bet everything", "leverage everything"
            ],
        }

        self.generic_risk_keywords = [
            "illegal", "secret", "guarantee", "risk free", "manipulate",
            "insider", "leak", "fraud", "launder", "scam"
        ]

    def check(self, query: str):
        query_lower = query.lower()

        for category, patterns in self.blocked_patterns.items():
            for pattern in patterns:
                # Token-based match (better than exact phrase)
                words = pattern.split()
                if any(word in query_lower for word in words):
                    return SafetyVerdict(
                        blocked=True,
                        category=category,
                        message=self._response(category)
                    )

        for word in self.generic_risk_keywords:
            if word in query_lower:
                return SafetyVerdict(
                    blocked=True,
                    category="generic_risk",
                    message="This request involves potentially harmful or illegal financial activity."
                )

        return SafetyVerdict(blocked=False)

    def _response(self, category):
        responses = {
            "insider_trading": "I cannot assist with insider or non-public information.",
            "market_manipulation": "I cannot help with market manipulation or artificial price actions.",
            "money_laundering": "I cannot assist with money laundering or hiding illegal funds.",
            "guaranteed_returns": "No investment can guarantee returns. Please be cautious.",
            "financial_fraud": "I cannot support fraudulent or deceptive financial activities.",
            "illegal_advice": "I cannot help with illegal financial or tax practices.",
            "high_risk_behavior": "This approach is extremely risky and not advisable.",
            "generic_risk": "This request involves potentially harmful or illegal financial activity."
        }

        return responses.get(category, "Request cannot be processed.")
    
_guard_instance = SafetyGuard()

def check(query: str):
    return _guard_instance.check(query)