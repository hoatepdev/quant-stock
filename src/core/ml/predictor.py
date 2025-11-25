"""Machine learning models for stock price prediction."""
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from src.database.models import DailyPrice, Factor
from src.utils.logger import get_logger

logger = get_logger(__name__)


class StockPredictor:
    """ML-based stock price predictor."""

    def __init__(self, db: Session):
        """Initialize predictor.

        Args:
            db: Database session
        """
        self.db = db
        self.model = None
        self.scaler = None
        self.feature_columns = []

    def prepare_features(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        lookback_days: int = 20,
    ) -> Optional[pd.DataFrame]:
        """Prepare feature matrix for ML model.

        Args:
            ticker: Stock ticker
            start_date: Start date
            end_date: End date
            lookback_days: Number of days to look back for features

        Returns:
            DataFrame with features or None
        """
        logger.info(f"Preparing features for {ticker} from {start_date} to {end_date}")

        # Fetch price data
        prices = (
            self.db.query(DailyPrice)
            .filter(
                DailyPrice.ticker == ticker,
                DailyPrice.date >= start_date - timedelta(days=lookback_days * 2),
                DailyPrice.date <= end_date,
            )
            .order_by(DailyPrice.date)
            .all()
        )

        if len(prices) < lookback_days:
            logger.warning(f"Insufficient price data for {ticker}")
            return None

        # Convert to DataFrame
        df = pd.DataFrame([
            {
                "date": p.date,
                "open": float(p.open),
                "high": float(p.high),
                "low": float(p.low),
                "close": float(p.close),
                "volume": p.volume,
            }
            for p in prices
        ])

        df = df.set_index("date")

        # Create technical features
        df = self._add_technical_features(df, lookback_days)

        # Fetch fundamental factors
        factors = (
            self.db.query(Factor)
            .filter(
                Factor.ticker == ticker,
                Factor.date >= start_date,
                Factor.date <= end_date,
            )
            .all()
        )

        if factors:
            factor_df = pd.DataFrame([
                {
                    "date": f.date,
                    "factor_name": f.factor_name,
                    "value": f.value,
                }
                for f in factors
            ])

            # Pivot factors
            factor_pivot = factor_df.pivot(
                index="date",
                columns="factor_name",
                values="value"
            )

            # Merge with price data
            df = df.join(factor_pivot, how="left")

        # Drop rows with NaN (from technical indicators)
        df = df.dropna()

        # Filter to requested date range
        df = df[(df.index >= start_date) & (df.index <= end_date)]

        return df

    def _add_technical_features(
        self,
        df: pd.DataFrame,
        lookback: int = 20,
    ) -> pd.DataFrame:
        """Add technical indicator features.

        Args:
            df: Price DataFrame
            lookback: Lookback period

        Returns:
            DataFrame with added features
        """
        # Returns
        df["return_1d"] = df["close"].pct_change(1)
        df["return_5d"] = df["close"].pct_change(5)
        df["return_20d"] = df["close"].pct_change(20)

        # Moving averages
        df["sma_5"] = df["close"].rolling(window=5).mean()
        df["sma_20"] = df["close"].rolling(window=20).mean()
        df["sma_50"] = df["close"].rolling(window=50).mean()

        # MA ratios
        df["sma_ratio_5_20"] = df["sma_5"] / df["sma_20"]
        df["sma_ratio_20_50"] = df["sma_20"] / df["sma_50"]

        # Volatility
        df["volatility_20"] = df["return_1d"].rolling(window=20).std()

        # Volume features
        df["volume_sma_20"] = df["volume"].rolling(window=20).mean()
        df["volume_ratio"] = df["volume"] / df["volume_sma_20"]

        # RSI
        df["rsi_14"] = self._calculate_rsi(df["close"], 14)

        # MACD
        df["macd"], df["macd_signal"] = self._calculate_macd(df["close"])
        df["macd_diff"] = df["macd"] - df["macd_signal"]

        # Bollinger Bands
        df["bb_upper"], df["bb_middle"], df["bb_lower"] = self._calculate_bollinger_bands(
            df["close"], 20
        )
        df["bb_position"] = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])

        # Price momentum
        df["momentum_5"] = df["close"] - df["close"].shift(5)
        df["momentum_20"] = df["close"] - df["close"].shift(20)

        return df

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _calculate_macd(
        self,
        prices: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ) -> Tuple[pd.Series, pd.Series]:
        """Calculate MACD indicator."""
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()

        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()

        return macd, signal_line

    def _calculate_bollinger_bands(
        self,
        prices: pd.Series,
        period: int = 20,
        std_dev: float = 2.0,
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands."""
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()

        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)

        return upper, middle, lower

    def train_model(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        model_type: str = "random_forest",
        target_days: int = 5,
    ) -> Dict:
        """Train ML model for price prediction.

        Args:
            ticker: Stock ticker
            start_date: Training start date
            end_date: Training end date
            model_type: Type of model (random_forest, gradient_boosting, linear)
            target_days: Predict N days ahead

        Returns:
            Dictionary with training results
        """
        logger.info(f"Training {model_type} model for {ticker}")

        # Prepare features
        df = self.prepare_features(ticker, start_date, end_date)

        if df is None or len(df) < 100:
            logger.error("Insufficient data for training")
            return {"error": "Insufficient data"}

        # Create target variable (future return)
        df["target"] = df["close"].shift(-target_days).pct_change(target_days)

        # Drop rows without target
        df = df.dropna()

        if len(df) < 50:
            logger.error("Insufficient samples after creating target")
            return {"error": "Insufficient samples"}

        # Select features
        feature_cols = [
            col for col in df.columns
            if col not in ["target", "open", "high", "low", "close", "volume"]
        ]

        X = df[feature_cols].values
        y = df["target"].values

        # Split train/test
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        # Scale features
        try:
            from sklearn.preprocessing import StandardScaler
            self.scaler = StandardScaler()
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
        except ImportError:
            logger.warning("scikit-learn not available, skipping scaling")
            X_train_scaled = X_train
            X_test_scaled = X_test

        # Train model
        try:
            if model_type == "random_forest":
                from sklearn.ensemble import RandomForestRegressor
                self.model = RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42,
                    n_jobs=-1
                )
            elif model_type == "gradient_boosting":
                from sklearn.ensemble import GradientBoostingRegressor
                self.model = GradientBoostingRegressor(
                    n_estimators=100,
                    max_depth=5,
                    random_state=42
                )
            elif model_type == "linear":
                from sklearn.linear_model import Ridge
                self.model = Ridge(alpha=1.0)
            else:
                logger.error(f"Unknown model type: {model_type}")
                return {"error": f"Unknown model type: {model_type}"}

            # Train
            self.model.fit(X_train_scaled, y_train)
            self.feature_columns = feature_cols

            # Evaluate
            train_score = self.model.score(X_train_scaled, y_train)
            test_score = self.model.score(X_test_scaled, y_test)

            # Predictions
            y_pred = self.model.predict(X_test_scaled)

            # Calculate metrics
            from sklearn.metrics import mean_squared_error, mean_absolute_error

            mse = mean_squared_error(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mse)

            # Feature importance
            if hasattr(self.model, "feature_importances_"):
                importances = self.model.feature_importances_
                feature_importance = {
                    feature_cols[i]: float(importances[i])
                    for i in range(len(feature_cols))
                }
                # Sort by importance
                feature_importance = dict(
                    sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
                )
            else:
                feature_importance = {}

            results = {
                "model_type": model_type,
                "ticker": ticker,
                "train_samples": len(X_train),
                "test_samples": len(X_test),
                "train_r2": float(train_score),
                "test_r2": float(test_score),
                "rmse": float(rmse),
                "mae": float(mae),
                "target_days": target_days,
                "features_used": len(feature_cols),
                "feature_importance": feature_importance,
            }

            logger.info(
                f"Model trained successfully. "
                f"Test R²: {test_score:.4f}, RMSE: {rmse:.4f}"
            )

            return results

        except ImportError:
            logger.error("scikit-learn required for ML models")
            return {"error": "scikit-learn not installed"}
        except Exception as e:
            logger.error(f"Error training model: {e}")
            return {"error": str(e)}

    def predict(
        self,
        ticker: str,
        prediction_date: Optional[date] = None,
    ) -> Optional[Dict]:
        """Make prediction for a stock.

        Args:
            ticker: Stock ticker
            prediction_date: Date to make prediction from (default: latest)

        Returns:
            Dictionary with prediction or None
        """
        if self.model is None:
            logger.error("Model not trained yet")
            return None

        if prediction_date is None:
            prediction_date = date.today()

        # Prepare features for prediction
        start_date = prediction_date - timedelta(days=100)
        df = self.prepare_features(ticker, start_date, prediction_date)

        if df is None or len(df) == 0:
            logger.error(f"No data available for prediction")
            return None

        # Get latest features
        latest_features = df[self.feature_columns].iloc[-1].values.reshape(1, -1)

        # Scale if scaler available
        if self.scaler:
            latest_features = self.scaler.transform(latest_features)

        # Predict
        prediction = self.model.predict(latest_features)[0]

        # Get current price
        current_price = df["close"].iloc[-1]

        return {
            "ticker": ticker,
            "prediction_date": prediction_date,
            "current_price": float(current_price),
            "predicted_return": float(prediction),
            "predicted_direction": "UP" if prediction > 0 else "DOWN",
            "confidence": "medium",  # Could calculate from prediction interval
        }

    def predict_multiple(
        self,
        tickers: List[str],
        prediction_date: Optional[date] = None,
    ) -> List[Dict]:
        """Make predictions for multiple stocks.

        Args:
            tickers: List of tickers
            prediction_date: Date to make prediction from

        Returns:
            List of prediction dictionaries
        """
        predictions = []

        for ticker in tickers:
            try:
                pred = self.predict(ticker, prediction_date)
                if pred:
                    predictions.append(pred)
            except Exception as e:
                logger.warning(f"Error predicting {ticker}: {e}")

        return predictions
