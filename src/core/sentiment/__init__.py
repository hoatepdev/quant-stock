"""Sentiment analysis module."""
from src.core.sentiment.analyzer import (
    NewsAggregator,
    SentimentAnalyzer,
    SentimentSignalGenerator,
)

__all__ = ["SentimentAnalyzer", "NewsAggregator", "SentimentSignalGenerator"]
