"""Corporate action detection logic."""
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

import pandas as pd
from sqlalchemy.orm import Session

from src.database.models import CorporateAction, DailyPrice
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CorporateActionDetector:
    """Detect corporate actions from price and volume patterns."""

    def __init__(self, db: Session):
        """Initialize detector.

        Args:
            db: Database session
        """
        self.db = db

    def detect_stock_splits(
        self,
        ticker: str,
        price_gap_threshold: float = 0.30,
        volume_spike_threshold: float = 2.0,
    ) -> List[Dict]:
        """Detect stock splits from price gaps and volume spikes.

        Args:
            ticker: Stock ticker symbol
            price_gap_threshold: Minimum price gap to consider (default 30%)
            volume_spike_threshold: Minimum volume spike multiplier (default 2x)

        Returns:
            List of detected split events
        """
        # Fetch price data
        prices = (
            self.db.query(DailyPrice)
            .filter(DailyPrice.ticker == ticker)
            .order_by(DailyPrice.date)
            .all()
        )

        if len(prices) < 2:
            return []

        detected_splits = []

        # Convert to DataFrame for easier analysis
        df = pd.DataFrame([
            {
                "date": p.date,
                "close": float(p.close),
                "volume": p.volume,
            }
            for p in prices
        ])

        df = df.sort_values("date")

        # Calculate metrics
        df["price_change_pct"] = df["close"].pct_change().abs()
        df["volume_ma20"] = df["volume"].rolling(window=20, min_periods=1).mean()
        df["volume_ratio"] = df["volume"] / df["volume_ma20"]

        # Detect downward price gaps (potential splits)
        for idx in range(1, len(df)):
            price_drop_pct = (df.iloc[idx-1]["close"] - df.iloc[idx]["close"]) / df.iloc[idx-1]["close"]
            volume_spike = df.iloc[idx]["volume_ratio"]

            # Check for split pattern: large price drop + volume spike
            if price_drop_pct >= price_gap_threshold and volume_spike >= volume_spike_threshold:
                # Estimate split ratio
                ratio = df.iloc[idx-1]["close"] / df.iloc[idx]["close"]

                detected_splits.append({
                    "ticker": ticker,
                    "ex_date": df.iloc[idx]["date"],
                    "action_type": "SPLIT",
                    "estimated_ratio": round(ratio, 4),
                    "price_before": df.iloc[idx-1]["close"],
                    "price_after": df.iloc[idx]["close"],
                    "price_drop_pct": price_drop_pct * 100,
                    "volume_spike": volume_spike,
                    "detection_method": "AUTOMATIC",
                })

                logger.info(
                    f"Detected potential stock split for {ticker} on {df.iloc[idx]['date']}: "
                    f"{ratio:.2f}:1 ratio"
                )

        return detected_splits

    def detect_reverse_splits(
        self,
        ticker: str,
        price_jump_threshold: float = 0.30,
    ) -> List[Dict]:
        """Detect reverse stock splits from sudden price increases.

        Args:
            ticker: Stock ticker symbol
            price_jump_threshold: Minimum price jump to consider (default 30%)

        Returns:
            List of detected reverse split events
        """
        # Fetch price data
        prices = (
            self.db.query(DailyPrice)
            .filter(DailyPrice.ticker == ticker)
            .order_by(DailyPrice.date)
            .all()
        )

        if len(prices) < 2:
            return []

        detected_reverse_splits = []

        # Convert to DataFrame
        df = pd.DataFrame([
            {
                "date": p.date,
                "close": float(p.close),
                "volume": p.volume,
            }
            for p in prices
        ])

        df = df.sort_values("date")

        # Detect upward price gaps (potential reverse splits)
        for idx in range(1, len(df)):
            price_jump_pct = (df.iloc[idx]["close"] - df.iloc[idx-1]["close"]) / df.iloc[idx-1]["close"]

            if price_jump_pct >= price_jump_threshold:
                # Estimate reverse split ratio
                ratio = df.iloc[idx]["close"] / df.iloc[idx-1]["close"]

                detected_reverse_splits.append({
                    "ticker": ticker,
                    "ex_date": df.iloc[idx]["date"],
                    "action_type": "REVERSE_SPLIT",
                    "estimated_ratio": round(ratio, 4),
                    "price_before": df.iloc[idx-1]["close"],
                    "price_after": df.iloc[idx]["close"],
                    "price_jump_pct": price_jump_pct * 100,
                    "detection_method": "AUTOMATIC",
                })

                logger.info(
                    f"Detected potential reverse split for {ticker} on {df.iloc[idx]['date']}: "
                    f"1:{ratio:.2f} ratio"
                )

        return detected_reverse_splits

    def save_detected_actions(self, detected_actions: List[Dict]) -> int:
        """Save detected corporate actions to database.

        Args:
            detected_actions: List of detected action dictionaries

        Returns:
            Number of actions saved
        """
        saved_count = 0

        for action_data in detected_actions:
            # Check if action already exists
            existing = (
                self.db.query(CorporateAction)
                .filter(
                    CorporateAction.ticker == action_data["ticker"],
                    CorporateAction.ex_date == action_data["ex_date"],
                    CorporateAction.action_type == action_data["action_type"],
                )
                .first()
            )

            if not existing:
                # Calculate adjustment factor
                adjustment_factor = self._calculate_adjustment_factor(action_data)

                new_action = CorporateAction(
                    ticker=action_data["ticker"],
                    ex_date=action_data["ex_date"],
                    action_type=action_data["action_type"],
                    ratio=Decimal(str(action_data.get("estimated_ratio", 0))),
                    adjustment_factor=adjustment_factor,
                    description=self._generate_description(action_data),
                    is_verified=False,  # Needs manual verification
                    is_applied=False,
                    detection_method="AUTOMATIC",
                )

                self.db.add(new_action)
                saved_count += 1

        self.db.commit()
        logger.info(f"Saved {saved_count} new corporate actions to database")

        return saved_count

    def _calculate_adjustment_factor(self, action_data: Dict) -> Decimal:
        """Calculate adjustment factor for corporate action.

        Args:
            action_data: Corporate action data

        Returns:
            Adjustment factor
        """
        action_type = action_data["action_type"]
        ratio = action_data.get("estimated_ratio", 1.0)

        if action_type == "SPLIT":
            # For splits, prices before the split need to be divided by ratio
            return Decimal(str(1.0 / ratio))
        elif action_type == "REVERSE_SPLIT":
            # For reverse splits, prices before need to be multiplied
            return Decimal(str(ratio))
        elif action_type == "BONUS_SHARE":
            # For bonus shares, adjust by (1 + bonus_ratio)
            return Decimal(str(1.0 / (1.0 + ratio)))
        else:
            return Decimal("1.0")

    def _generate_description(self, action_data: Dict) -> str:
        """Generate human-readable description of corporate action.

        Args:
            action_data: Corporate action data

        Returns:
            Description string
        """
        action_type = action_data["action_type"]
        ticker = action_data["ticker"]
        ratio = action_data.get("estimated_ratio", 1.0)

        if action_type == "SPLIT":
            return (
                f"Detected stock split for {ticker} with ratio {ratio:.2f}:1. "
                f"Price dropped {action_data.get('price_drop_pct', 0):.1f}% with "
                f"volume spike of {action_data.get('volume_spike', 0):.1f}x. "
                "Requires manual verification."
            )
        elif action_type == "REVERSE_SPLIT":
            return (
                f"Detected reverse split for {ticker} with ratio 1:{ratio:.2f}. "
                f"Price jumped {action_data.get('price_jump_pct', 0):.1f}%. "
                "Requires manual verification."
            )
        else:
            return f"Detected {action_type} for {ticker}. Requires manual verification."

    def run_detection_for_ticker(self, ticker: str) -> int:
        """Run all detection methods for a single ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Total number of actions detected and saved
        """
        logger.info(f"Running corporate action detection for {ticker}")

        all_detected = []

        # Detect splits
        splits = self.detect_stock_splits(ticker)
        all_detected.extend(splits)

        # Detect reverse splits
        reverse_splits = self.detect_reverse_splits(ticker)
        all_detected.extend(reverse_splits)

        # Save to database
        saved_count = self.save_detected_actions(all_detected)

        return saved_count
