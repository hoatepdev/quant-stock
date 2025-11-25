"""Sentiment analysis for news and social media."""
from datetime import date, datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from src.utils.logger import get_logger

logger = get_logger(__name__)


class SentimentAnalyzer:
    """Analyze sentiment from news and social media."""

    def __init__(self, db: Session):
        """Initialize sentiment analyzer.

        Args:
            db: Database session
        """
        self.db = db
        self.vietnamese_positive_words = self._load_vietnamese_positive_words()
        self.vietnamese_negative_words = self._load_vietnamese_negative_words()

    def _load_vietnamese_positive_words(self) -> set:
        """Load Vietnamese positive sentiment words."""
        return {
            "tăng", "tăng trưởng", "lợi nhuận", "tốt", "khả quan",
            "tích cực", "cải thiện", "phát triển", "mạnh mẽ", "vững chắc",
            "thành công", "hiệu quả", "cao", "tăng cao", "đột phá",
            "tiến bộ", "ưu việt", "xuất sắc", "tăng giá", "lạc quan",
        }

    def _load_vietnamese_negative_words(self) -> set:
        """Load Vietnamese negative sentiment words."""
        return {
            "giảm", "sụt giảm", "thua lỗ", "xấu", "bi quan",
            "tiêu cực", "suy giảm", "khó khăn", "yếu", "suy yếu",
            "thất bại", "kém", "thấp", "giảm giá", "lo ngại",
            "rủi ro", "nguy cơ", "suy thoái", "khủng hoảng", "thất vọng",
        }

    def analyze_text(self, text: str) -> Dict:
        """Analyze sentiment of Vietnamese text.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with sentiment scores
        """
        if not text:
            return {
                "sentiment": "neutral",
                "score": 0.0,
                "positive_count": 0,
                "negative_count": 0,
            }

        text_lower = text.lower()

        # Count positive and negative words
        positive_count = sum(
            1 for word in self.vietnamese_positive_words
            if word in text_lower
        )

        negative_count = sum(
            1 for word in self.vietnamese_negative_words
            if word in text_lower
        )

        # Calculate sentiment score
        total_words = positive_count + negative_count

        if total_words == 0:
            sentiment_score = 0.0
            sentiment = "neutral"
        else:
            sentiment_score = (positive_count - negative_count) / total_words

            if sentiment_score > 0.2:
                sentiment = "positive"
            elif sentiment_score < -0.2:
                sentiment = "negative"
            else:
                sentiment = "neutral"

        return {
            "sentiment": sentiment,
            "score": sentiment_score,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "confidence": min(abs(sentiment_score), 1.0),
        }

    def analyze_news_headline(self, headline: str, ticker: str) -> Dict:
        """Analyze sentiment of news headline.

        Args:
            headline: News headline
            ticker: Stock ticker mentioned

        Returns:
            Sentiment analysis result
        """
        result = self.analyze_text(headline)
        result["ticker"] = ticker
        result["headline"] = headline
        result["analyzed_at"] = datetime.now()

        return result

    def analyze_multiple_headlines(
        self,
        headlines: List[str],
        ticker: str,
    ) -> Dict:
        """Analyze sentiment of multiple headlines for a stock.

        Args:
            headlines: List of news headlines
            ticker: Stock ticker

        Returns:
            Aggregated sentiment analysis
        """
        if not headlines:
            return {
                "ticker": ticker,
                "overall_sentiment": "neutral",
                "average_score": 0.0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "total_headlines": 0,
            }

        sentiments = [self.analyze_text(h) for h in headlines]

        positive_count = sum(1 for s in sentiments if s["sentiment"] == "positive")
        negative_count = sum(1 for s in sentiments if s["sentiment"] == "negative")
        neutral_count = sum(1 for s in sentiments if s["sentiment"] == "neutral")

        average_score = sum(s["score"] for s in sentiments) / len(sentiments)

        if average_score > 0.2:
            overall_sentiment = "positive"
        elif average_score < -0.2:
            overall_sentiment = "negative"
        else:
            overall_sentiment = "neutral"

        return {
            "ticker": ticker,
            "overall_sentiment": overall_sentiment,
            "average_score": average_score,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "total_headlines": len(headlines),
            "sentiment_ratio": positive_count / len(headlines) if headlines else 0,
        }

    def get_sentiment_signal(self, ticker: str, headlines: List[str]) -> str:
        """Get trading signal based on sentiment.

        Args:
            ticker: Stock ticker
            headlines: Recent headlines

        Returns:
            Trading signal: BUY, SELL, or HOLD
        """
        analysis = self.analyze_multiple_headlines(headlines, ticker)

        score = analysis["average_score"]
        ratio = analysis["sentiment_ratio"]

        # Strong positive sentiment
        if score > 0.5 and ratio > 0.6:
            return "BUY"

        # Strong negative sentiment
        elif score < -0.5 or ratio < 0.3:
            return "SELL"

        # Neutral or mixed sentiment
        else:
            return "HOLD"

    def calculate_sentiment_momentum(
        self,
        ticker: str,
        recent_headlines: List[str],
        older_headlines: List[str],
    ) -> Dict:
        """Calculate sentiment momentum (change over time).

        Args:
            ticker: Stock ticker
            recent_headlines: Recent headlines
            older_headlines: Older headlines for comparison

        Returns:
            Sentiment momentum analysis
        """
        recent_analysis = self.analyze_multiple_headlines(recent_headlines, ticker)
        older_analysis = self.analyze_multiple_headlines(older_headlines, ticker)

        momentum = recent_analysis["average_score"] - older_analysis["average_score"]

        if momentum > 0.3:
            trend = "improving"
        elif momentum < -0.3:
            trend = "deteriorating"
        else:
            trend = "stable"

        return {
            "ticker": ticker,
            "recent_sentiment": recent_analysis["overall_sentiment"],
            "older_sentiment": older_analysis["overall_sentiment"],
            "momentum": momentum,
            "trend": trend,
            "recent_score": recent_analysis["average_score"],
            "older_score": older_analysis["average_score"],
        }


class NewsAggregator:
    """Aggregate news from multiple sources."""

    def __init__(self):
        """Initialize news aggregator."""
        self.sources = []

    def fetch_vietstock_news(self, ticker: str, limit: int = 10) -> List[Dict]:
        """Fetch news from VietStock (placeholder).

        Args:
            ticker: Stock ticker
            limit: Number of articles

        Returns:
            List of news articles
        """
        # Placeholder implementation
        # In production, integrate with VietStock API or web scraping
        logger.info(f"Fetching VietStock news for {ticker}")

        return [
            {
                "title": f"Sample news about {ticker}",
                "source": "vietstock",
                "published_at": datetime.now(),
                "url": f"https://vietstock.vn/news/{ticker}",
            }
        ]

    def fetch_cafef_news(self, ticker: str, limit: int = 10) -> List[Dict]:
        """Fetch news from CafeF (placeholder).

        Args:
            ticker: Stock ticker
            limit: Number of articles

        Returns:
            List of news articles
        """
        logger.info(f"Fetching CafeF news for {ticker}")

        return [
            {
                "title": f"Sample CafeF news about {ticker}",
                "source": "cafef",
                "published_at": datetime.now(),
                "url": f"https://cafef.vn/news/{ticker}",
            }
        ]

    def fetch_all_news(self, ticker: str, limit: int = 20) -> List[Dict]:
        """Fetch news from all sources.

        Args:
            ticker: Stock ticker
            limit: Total number of articles

        Returns:
            Aggregated news list
        """
        news = []

        # Fetch from multiple sources
        news.extend(self.fetch_vietstock_news(ticker, limit // 2))
        news.extend(self.fetch_cafef_news(ticker, limit // 2))

        # Sort by date
        news.sort(key=lambda x: x["published_at"], reverse=True)

        return news[:limit]


class SentimentSignalGenerator:
    """Generate trading signals based on sentiment analysis."""

    def __init__(self, db: Session):
        """Initialize signal generator.

        Args:
            db: Database session
        """
        self.analyzer = SentimentAnalyzer(db)
        self.news_aggregator = NewsAggregator()

    def generate_signals(
        self,
        tickers: List[str],
        news_lookback_days: int = 7,
    ) -> List[Dict]:
        """Generate sentiment-based trading signals.

        Args:
            tickers: List of stock tickers
            news_lookback_days: Days of news to analyze

        Returns:
            List of signal dictionaries
        """
        signals = []

        for ticker in tickers:
            try:
                # Fetch recent news
                news = self.news_aggregator.fetch_all_news(ticker, limit=20)

                if not news:
                    logger.warning(f"No news found for {ticker}")
                    continue

                # Extract headlines
                headlines = [article["title"] for article in news]

                # Analyze sentiment
                sentiment_analysis = self.analyzer.analyze_multiple_headlines(
                    headlines, ticker
                )

                # Get trading signal
                signal = self.analyzer.get_sentiment_signal(ticker, headlines)

                signals.append({
                    "ticker": ticker,
                    "signal": signal,
                    "sentiment": sentiment_analysis["overall_sentiment"],
                    "sentiment_score": sentiment_analysis["average_score"],
                    "confidence": abs(sentiment_analysis["average_score"]),
                    "news_count": len(headlines),
                    "generated_at": datetime.now(),
                })

            except Exception as e:
                logger.error(f"Error generating signal for {ticker}: {e}")

        return signals

    def get_sentiment_rankings(
        self,
        tickers: List[str],
    ) -> List[Dict]:
        """Rank stocks by sentiment score.

        Args:
            tickers: List of stock tickers

        Returns:
            Sorted list of stocks by sentiment
        """
        signals = self.generate_signals(tickers)

        # Sort by sentiment score
        signals.sort(key=lambda x: x["sentiment_score"], reverse=True)

        return signals
