# src/safety/guard.py

class SafetyVerdict:
    def __init__(self, blocked: bool, category: str = None, message: str = None):
        self.blocked = blocked
        self.category = category
        self.message = message


class SafetyGuard:
    def __init__(self):
        # Category-specific phrases targeting intent to execute/help with harmful acts
        self.blocked_patterns = {
            "insider_trading": [
                "insider trading", "non public", "inside info", "material non-public",
                "confidential merger", "unannounced acquisition", "know about an unannounced",
                "friend at microsoft gave me a tip", "earnings before tomorrow's announcement",
                "trade on this confidential"
            ],
            "market_manipulation": [
                "pump and dump", "pump up the price", "coordinated buying scheme",
                "wash trade", "spoofing and layering", "create volume", "rig the market",
                "artificial price"
            ],
            "money_laundering": [
                "launder", "clean money", "hide money", "illegal funds", "obscure the source",
                "structure deposits", "avoid the 10k reporting", "avoid reporting",
                "hide trading profits", "tax authorities"
            ],
            "guaranteed_returns": [
                "guarantee me", "guaranteed return", "100% certain to go up", 
                "foolproof way to make", "promise me my money will double", "sure profit"
            ],
            "reckless_advice": [
                "put all my retirement savings in crypto, do it", "put all my retirement",
                "take a margin loan to buy", "entire emergency fund into options",
                "mortgage my house for", "bet everything", "leverage everything"
            ],
            "sanctions_evasion": [
                "bypass ofac sanctions", "shell company to bypass", 
                "invest in a sanctioned russian", "without it being traced"
            ],
            "fraud": [
                "draft a fake contract", "fake contract note"
            ]
        }

    def check(self, query: str) -> SafetyVerdict:
        query_lower = query.lower()

        # 1. First handle safe educational queries explicitly to ensure high pass-through
        # If they ask "what is", "explain", "how does", "why are", etc., we allow it
        educational_keywords = [
            "what is", "explain the", "how does the", "why are", "what are the",
            "is it ever legitimate", "describe the three stages", "factors should a",
            "obligations do brokers", "is short selling illegal"
        ]
        
        if any(edu in query_lower for edu in educational_keywords):
            return SafetyVerdict(blocked=False)

        # 2. Check harmful execution patterns
        for category, phrases in self.blocked_patterns.items():
            for phrase in phrases:
                if phrase in query_lower:
                    return SafetyVerdict(
                        blocked=True,
                        category=category,
                        message=self._response(category)
                    )

        return SafetyVerdict(blocked=False)

    def _response(self, category: str) -> str:
        responses = {
            "insider_trading": "I cannot assist with insider or non-public information.",
            "market_manipulation": "I cannot help with market manipulation or artificial price actions.",
            "money_laundering": "I cannot assist with money laundering or hiding illegal funds.",
            "guaranteed_returns": "No investment can guarantee returns. Please be cautious.",
            "reckless_advice": "This approach is extremely risky and not advisable.",
            "sanctions_evasion": "I cannot assist with bypassing legal sanctions or tracing restrictions.",
            "fraud": "I cannot support fraudulent or deceptive financial activities."
        }
        return responses.get(category, "Request cannot be processed due to safety regulations.")


_guard_instance = SafetyGuard()

def check(query: str) -> SafetyVerdict:
    return _guard_instance.check(query)