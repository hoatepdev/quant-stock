Build a Vietnamese text sentiment analysis system for stock market news:

**Data sources:**

- VnExpress Economy
- CafeF news
- Vietnamese stock forums (vn.investing.com)
- Social media (if accessible)

**Requirements:**

1. Vietnamese text preprocessing using underthesea, pyvi
2. Sentiment classification (positive/negative/neutral)
3. Named entity recognition for stock tickers
4. Topic modeling for market themes
5. Sentiment aggregation by ticker and sector
6. Time-series sentiment tracking

**Model approach:**

- Use PhoBERT or Vietnamese BERT models
- Fine-tune on Vietnamese financial text
- Ensemble with rule-based VADER adaptation

**Output:**

- Daily sentiment scores per ticker
- Market-wide sentiment index
- Sentiment change alerts
- Historical sentiment database

Provide data pipeline + model training code + inference API.
