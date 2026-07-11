
class ClassificationResult:
    def __init__(self, intent, agent, entities, safety="safe"):
        self.intent = intent
        self.agent = agent
        self.entities = entities
        self.safety = safety


def classify(query: str, llm=None):
    q = query.lower().strip()
    entities = extract_entities(query)

    # ----------------------------
    # GIBBERISH → GENERAL
    # ----------------------------
    if len(q) > 5 and q.isalpha() and " " not in q:
        return ClassificationResult("general_query", "general_query", {})

    # ----------------------------
    # TICKER ONLY → MARKET
    # ----------------------------
    if len(q.split()) == 1 and entities["tickers"]:
        return ClassificationResult("market_research", "market_research", entities)

    # ----------------------------
    # GENERAL QUERY (EDUCATIONAL)
    # ----------------------------
    if q in ["hi", "hello", "thanks"]:
        return ClassificationResult("general_query", "general_query", {})

    if any(x in q for x in [
        "what is", "explain", "meaning", "difference"
    ]) and not any(x in q for x in [
        "price", "stock", "market", "invest"
    ]):
        return ClassificationResult("general_query", "general_query", {})

    # ----------------------------
    # CUSTOMER SUPPORT
    # ----------------------------
    if any(x in q for x in [
        "login", "account", "bank", "transaction",
        "didn't go through", "not working"
    ]):
        return ClassificationResult("customer_support", "customer_support", {})

    # ----------------------------
    # PORTFOLIO HEALTH (HIGH PRIORITY)
    # ----------------------------
    if any(x in q for x in [
        "my portfolio", "my holdings", "portfolio summary",
        "how am i doing", "diversified", "beating the market",
        "health check", "my investments", "concentration"
    ]):
        return ClassificationResult("portfolio_health", "portfolio_health", {})

    # ----------------------------
    # INVESTMENT STRATEGY
    # ----------------------------
    if any(x in q for x in [
        "should i", "buy", "sell", "rebalance", "hedge",
        "good time to invest"
    ]):
        return ClassificationResult("investment_strategy", "investment_strategy", entities)

    # ----------------------------
    # PRODUCT RECOMMENDATION
    # ----------------------------
    if any(x in q for x in [
        "recommend", "which fund", "best fund",
        "etf", "index fund"
    ]) and "market" not in q:
        return ClassificationResult("product_recommendation", "product_recommendation", {})

    # ----------------------------
    # FINANCIAL CALCULATOR
    # ----------------------------
    if any(x in q for x in [
        "calculate", "future value", "compound",
        "convert", "mortgage", "roi", "interest",
        "invest monthly", "years at", "tax"
    ]):
        return ClassificationResult("financial_calculator", "financial_calculator", {})

    # ----------------------------
    # FINANCIAL PLANNING
    # ----------------------------
    if any(x in q for x in [
        "retire", "retirement", "college", "education",
        "house", "fire", "save", "on track"
    ]):
        return ClassificationResult("financial_planning", "financial_planning", {})

    # ----------------------------
    # PREDICTIVE ANALYSIS
    # ----------------------------
    if any(x in q for x in [
        "predict", "forecast", "will be", "where will"
    ]):
        return ClassificationResult("predictive_analysis", "predictive_analysis", {})

    # ----------------------------
    # RISK ASSESSMENT
    # ----------------------------
    if any(x in q for x in [
        "risk", "beta", "drawdown", "stress test",
        "downside", "exposed", "drop"
    ]):
        return ClassificationResult("risk_assessment", "risk_assessment", {})

    # ----------------------------
    # MARKET RESEARCH (DEFAULT)
    # ----------------------------
    return ClassificationResult(
        "market_research",
        "market_research",
        entities
    )


# ----------------------------
# ENTITY EXTRACTION
# ----------------------------
def extract_entities(query: str):
    words = query.split()

    tickers = []
    for w in words:
        if w.isupper() and 1 <= len(w) <= 7:
            tickers.append(w)

    return {"tickers": tickers}