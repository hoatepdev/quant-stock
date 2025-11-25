"""Phase 3 features demonstration script."""
import asyncio
import sys
from datetime import date, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.analytics.performance import PerformanceAnalytics
from src.core.ml.predictor import StockPredictor
from src.core.realtime.feed import MarketDataStream, PriceAlert, RealtimeDataFeed
from src.core.screening.advanced_strategies import AdvancedScreener
from src.core.sentiment.analyzer import SentimentAnalyzer, SentimentSignalGenerator
from src.database.connection import get_sync_session
from src.utils.config import get_settings
from src.utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)
settings = get_settings()


def demo_ml_prediction():
    """Demonstrate machine learning price prediction."""
    logger.info("=== Machine Learning Prediction Demo ===")

    db = next(get_sync_session())
    predictor = StockPredictor(db)

    ticker = "VCB"
    end_date = date.today()
    start_date = end_date - timedelta(days=730)  # 2 years

    logger.info(f"Training ML model for {ticker}")

    # Train model
    results = predictor.train_model(
        ticker,
        start_date,
        end_date,
        model_type="random_forest",
        target_days=5,
    )

    if "error" not in results:
        logger.info(f"\nTraining Results:")
        logger.info(f"  Model: {results['model_type']}")
        logger.info(f"  Test R²: {results['test_r2']:.4f}")
        logger.info(f"  RMSE: {results['rmse']:.4f}")
        logger.info(f"  Features used: {results['features_used']}")

        # Show top features
        if results.get("feature_importance"):
            logger.info(f"\nTop 5 Important Features:")
            for i, (feature, importance) in enumerate(
                list(results["feature_importance"].items())[:5]
            ):
                logger.info(f"  {i+1}. {feature}: {importance:.4f}")

        # Make prediction
        logger.info(f"\nMaking prediction for {ticker}...")
        prediction = predictor.predict(ticker)

        if prediction:
            logger.info(f"  Current Price: {prediction['current_price']:.2f}")
            logger.info(f"  Predicted Return (5d): {prediction['predicted_return']:.2%}")
            logger.info(f"  Direction: {prediction['predicted_direction']}")

    db.close()
    logger.info("\nML prediction demo complete\n")


def demo_sentiment_analysis():
    """Demonstrate sentiment analysis."""
    logger.info("=== Sentiment Analysis Demo ===")

    db = next(get_sync_session())
    analyzer = SentimentAnalyzer(db)

    # Sample Vietnamese news headlines
    headlines = [
        "VCB tăng trưởng lợi nhuận mạnh mẽ trong quý 4",
        "Triển vọng tích cực cho ngành ngân hàng năm 2025",
        "VCB công bố kết quả kinh doanh ấn tượng",
        "Thị trường chứng khoán khó khăn trong ngắn hạn",
        "VCB được nâng hạng tín nhiệm",
    ]

    logger.info("Analyzing Vietnamese news headlines...")

    # Analyze individual headlines
    for headline in headlines:
        result = analyzer.analyze_text(headline)
        logger.info(f"\nHeadline: {headline}")
        logger.info(f"  Sentiment: {result['sentiment']}")
        logger.info(f"  Score: {result['score']:.2f}")

    # Aggregate analysis
    logger.info("\nAggregate Analysis for VCB:")
    aggregate = analyzer.analyze_multiple_headlines(headlines, "VCB")
    logger.info(f"  Overall Sentiment: {aggregate['overall_sentiment']}")
    logger.info(f"  Average Score: {aggregate['average_score']:.2f}")
    logger.info(f"  Positive: {aggregate['positive_count']}")
    logger.info(f"  Negative: {aggregate['negative_count']}")
    logger.info(f"  Neutral: {aggregate['neutral_count']}")

    # Get trading signal
    signal = analyzer.get_sentiment_signal("VCB", headlines)
    logger.info(f"  Trading Signal: {signal}")

    # Generate signals for multiple stocks
    logger.info("\nGenerating sentiment signals...")
    signal_gen = SentimentSignalGenerator(db)
    signals = signal_gen.generate_signals(["VCB", "VHM", "VIC"])

    for sig in signals:
        logger.info(
            f"  {sig['ticker']}: {sig['signal']} "
            f"(Sentiment: {sig['sentiment']}, Score: {sig['sentiment_score']:.2f})"
        )

    db.close()
    logger.info("\nSentiment analysis demo complete\n")


async def demo_realtime_feed():
    """Demonstrate real-time data feed."""
    logger.info("=== Real-time Data Feed Demo ===")

    feed = RealtimeDataFeed()

    # Create price alert system
    alert_system = PriceAlert(feed)

    # Add some alerts
    logger.info("Setting up price alerts...")

    async def alert_callback(ticker, price_data, alert):
        logger.info(
            f"  ALERT TRIGGERED! {ticker} {alert['type']} "
            f"{alert['threshold']} - Current: {price_data['price']}"
        )

    alert_system.add_alert("VCB", "price_above", 100, alert_callback)
    alert_system.add_alert("VCB", "change_pct", 3, alert_callback)

    logger.info("  Alert 1: VCB price above 100")
    logger.info("  Alert 2: VCB change > 3%")

    # Create market data stream
    stream = MarketDataStream(feed)

    # Simulate some price updates
    logger.info("\nSimulating price updates...")

    tickers = ["VCB", "VHM", "VIC"]

    for _ in range(3):
        for ticker in tickers:
            price_update = await feed._fetch_realtime_price(ticker)
            await feed.broadcast_price_update(ticker, price_update)

            logger.info(
                f"  {ticker}: {price_update['price']:.2f} "
                f"({price_update['change_pct']:+.2f}%)"
            )

        await asyncio.sleep(1)

    # Show market data bars
    logger.info("\nCurrent OHLC bars:")
    for ticker in tickers:
        bar = stream.get_current_bar(ticker)
        if bar:
            logger.info(
                f"  {ticker}: O={bar['open']:.2f} H={bar['high']:.2f} "
                f"L={bar['low']:.2f} C={bar['close']:.2f}"
            )

    logger.info("\nReal-time feed demo complete\n")


def demo_advanced_screening():
    """Demonstrate advanced screening strategies."""
    logger.info("=== Advanced Screening Demo ===")

    db = next(get_sync_session())
    screener = AdvancedScreener(db)

    # Run all screening strategies
    logger.info("Running advanced screening strategies...\n")

    strategies = screener.screen_all_strategies(exchange="HOSE", limit_per_strategy=5)

    for strategy_name, stocks in strategies.items():
        logger.info(f"{strategy_name.upper()} Stocks ({len(stocks)} found):")

        for stock in stocks:
            logger.info(f"  {stock['ticker']} - {stock['name']}")

            # Show relevant metrics
            if strategy_name == "value":
                logger.info(
                    f"    P/E: {stock.get('pe_ratio', 'N/A')}, "
                    f"P/B: {stock.get('pb_ratio', 'N/A')}, "
                    f"Div Yield: {stock.get('dividend_yield', 'N/A')}%"
                )
            elif strategy_name == "growth":
                logger.info(
                    f"    Rev Growth: {stock.get('revenue_growth_yoy', 'N/A')}%, "
                    f"EPS Growth: {stock.get('eps_growth_yoy', 'N/A')}%, "
                    f"ROE: {stock.get('roe', 'N/A')}%"
                )
            elif strategy_name == "momentum":
                logger.info(
                    f"    Returns: {stock.get('returns', 0):.2%}, "
                    f"Volume Trend: {stock.get('volume_trend', 0):.2%}"
                )

        logger.info("")

    db.close()
    logger.info("Advanced screening demo complete\n")


def demo_performance_analytics():
    """Demonstrate performance analytics."""
    logger.info("=== Performance Analytics Demo ===")

    db = next(get_sync_session())
    analytics = PerformanceAnalytics(db)

    tickers = ["VCB", "VHM", "VIC"]
    end_date = date.today()
    start_date = end_date - timedelta(days=365)

    logger.info(f"Analyzing performance from {start_date} to {end_date}\n")

    # Calculate metrics for each stock
    for ticker in tickers:
        logger.info(f"{ticker} Performance Metrics:")

        metrics = analytics.calculate_all_metrics(ticker, start_date, end_date)

        logger.info(f"  Total Return: {metrics['returns']['total']:.2%}" if metrics['returns']['total'] else "  Total Return: N/A")
        logger.info(f"  Annualized Return: {metrics['returns']['annualized']:.2%}" if metrics['returns']['annualized'] else "  Annualized Return: N/A")
        logger.info(f"  Volatility: {metrics['risk']['volatility']:.2%}" if metrics['risk']['volatility'] else "  Volatility: N/A")
        logger.info(f"  Sharpe Ratio: {metrics['risk']['sharpe_ratio']:.2f}" if metrics['risk']['sharpe_ratio'] else "  Sharpe Ratio: N/A")
        logger.info(f"  Max Drawdown: {metrics['risk']['max_drawdown']:.2%}" if metrics['risk']['max_drawdown'] else "  Max Drawdown: N/A")
        logger.info(f"  Beta: {metrics['risk']['beta']:.2f}" if metrics['risk']['beta'] else "  Beta: N/A")
        logger.info(f"  Alpha: {metrics['alpha']:.2%}" if metrics['alpha'] else "  Alpha: N/A")
        logger.info("")

    # Comparative analysis
    logger.info("Comparative Analysis:")
    comparison = analytics.compare_stocks(tickers, start_date, end_date)
    logger.info("\n" + comparison.to_string() if not comparison.empty else "No data available")

    db.close()
    logger.info("\nPerformance analytics demo complete\n")


def main():
    """Run all Phase 3 demos."""
    logger.info("Starting Phase 3 Features Demonstration\n")

    try:
        # Demo 1: ML Prediction
        demo_ml_prediction()

        # Demo 2: Sentiment Analysis
        demo_sentiment_analysis()

        # Demo 3: Real-time Feed
        asyncio.run(demo_realtime_feed())

        # Demo 4: Advanced Screening
        demo_advanced_screening()

        # Demo 5: Performance Analytics
        demo_performance_analytics()

        logger.info("All Phase 3 demos completed successfully!")

    except Exception as e:
        logger.error(f"Demo error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
