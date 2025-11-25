"""Corporate action price adjustment logic."""
from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from src.database.models import CorporateAction, DailyPrice
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CorporateActionAdjuster:
    """Apply corporate action adjustments to historical prices."""

    def __init__(self, db: Session):
        """Initialize adjuster.

        Args:
            db: Database session
        """
        self.db = db

    def apply_adjustments_for_ticker(
        self,
        ticker: str,
        verified_only: bool = True,
    ) -> int:
        """Apply all corporate action adjustments for a ticker.

        Args:
            ticker: Stock ticker symbol
            verified_only: Only apply verified actions (default True)

        Returns:
            Number of price records adjusted
        """
        logger.info(f"Applying corporate action adjustments for {ticker}")

        # Get all corporate actions for ticker
        query = self.db.query(CorporateAction).filter(
            CorporateAction.ticker == ticker,
            CorporateAction.is_applied == False,  # noqa: E712
        )

        if verified_only:
            query = query.filter(CorporateAction.is_verified == True)  # noqa: E712

        actions = query.order_by(CorporateAction.ex_date.desc()).all()

        if not actions:
            logger.info(f"No unapplied actions found for {ticker}")
            return 0

        total_adjusted = 0

        for action in actions:
            count = self._apply_single_action(action)
            total_adjusted += count

            # Mark action as applied
            action.is_applied = True
            action.applied_at = date.today()

        self.db.commit()

        logger.info(
            f"Applied {len(actions)} actions, adjusted {total_adjusted} price records for {ticker}"
        )

        return total_adjusted

    def _apply_single_action(self, action: CorporateAction) -> int:
        """Apply a single corporate action adjustment.

        Args:
            action: Corporate action to apply

        Returns:
            Number of price records adjusted
        """
        logger.info(
            f"Applying {action.action_type} for {action.ticker} "
            f"on {action.ex_date} with factor {action.adjustment_factor}"
        )

        # Get all prices before the ex-date
        prices_to_adjust = (
            self.db.query(DailyPrice)
            .filter(
                DailyPrice.ticker == action.ticker,
                DailyPrice.date < action.ex_date,
            )
            .all()
        )

        if not prices_to_adjust:
            logger.warning(f"No prices found before {action.ex_date} for {action.ticker}")
            return 0

        adjustment_factor = float(action.adjustment_factor)
        adjusted_count = 0

        for price in prices_to_adjust:
            # Update OHLC prices
            price.open = Decimal(str(float(price.open) * adjustment_factor))
            price.high = Decimal(str(float(price.high) * adjustment_factor))
            price.low = Decimal(str(float(price.low) * adjustment_factor))
            price.close = Decimal(str(float(price.close) * adjustment_factor))

            # Update adjusted_close or set it if not present
            if price.adjusted_close:
                price.adjusted_close = Decimal(
                    str(float(price.adjusted_close) * adjustment_factor)
                )
            else:
                price.adjusted_close = price.close

            # Update cumulative adjustment factor
            price.adjustment_factor = Decimal(
                str(float(price.adjustment_factor) * adjustment_factor)
            )

            adjusted_count += 1

        logger.info(f"Adjusted {adjusted_count} price records")

        return adjusted_count

    def recalculate_adjusted_prices(self, ticker: str) -> int:
        """Recalculate all adjusted prices from scratch.

        This is useful when you want to recompute all adjustments after
        making changes to corporate actions.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Number of price records recalculated
        """
        logger.info(f"Recalculating adjusted prices for {ticker}")

        # Reset all adjustments first
        prices = (
            self.db.query(DailyPrice)
            .filter(DailyPrice.ticker == ticker)
            .order_by(DailyPrice.date)
            .all()
        )

        if not prices:
            logger.warning(f"No prices found for {ticker}")
            return 0

        # Reset adjustment factors
        for price in prices:
            price.adjustment_factor = Decimal("1.0")
            price.adjusted_close = price.close

        # Get all verified actions in chronological order
        actions = (
            self.db.query(CorporateAction)
            .filter(
                CorporateAction.ticker == ticker,
                CorporateAction.is_verified == True,  # noqa: E712
            )
            .order_by(CorporateAction.ex_date)
            .all()
        )

        if not actions:
            logger.info(f"No verified actions for {ticker}, using unadjusted prices")
            self.db.commit()
            return len(prices)

        # Calculate cumulative adjustment factor for each date
        adjustment_map = {}
        cumulative_factor = Decimal("1.0")

        for action in actions:
            ex_date = action.ex_date
            cumulative_factor *= action.adjustment_factor
            adjustment_map[ex_date] = cumulative_factor

        # Apply adjustments
        adjusted_count = 0
        for price in prices:
            # Find the applicable adjustment factor
            applicable_factor = Decimal("1.0")

            for action_date, factor in adjustment_map.items():
                if price.date < action_date:
                    applicable_factor *= factor

            if applicable_factor != Decimal("1.0"):
                price.open = Decimal(str(float(price.open) * float(applicable_factor)))
                price.high = Decimal(str(float(price.high) * float(applicable_factor)))
                price.low = Decimal(str(float(price.low) * float(applicable_factor)))
                price.close = Decimal(str(float(price.close) * float(applicable_factor)))
                price.adjusted_close = price.close
                price.adjustment_factor = applicable_factor
                adjusted_count += 1

        # Mark all actions as applied
        for action in actions:
            action.is_applied = True
            action.applied_at = date.today()

        self.db.commit()

        logger.info(f"Recalculated {adjusted_count} adjusted prices for {ticker}")

        return adjusted_count

    def unapply_action(self, action_id: int) -> int:
        """Unapply a corporate action adjustment.

        Args:
            action_id: Corporate action ID

        Returns:
            Number of price records unadjusted
        """
        action = self.db.query(CorporateAction).filter(
            CorporateAction.id == action_id
        ).first()

        if not action:
            logger.error(f"Action {action_id} not found")
            return 0

        if not action.is_applied:
            logger.warning(f"Action {action_id} is not currently applied")
            return 0

        logger.info(
            f"Unapplying {action.action_type} for {action.ticker} on {action.ex_date}"
        )

        # Get all prices before the ex-date
        prices_to_unapply = (
            self.db.query(DailyPrice)
            .filter(
                DailyPrice.ticker == action.ticker,
                DailyPrice.date < action.ex_date,
            )
            .all()
        )

        if not prices_to_unapply:
            logger.warning(
                f"No prices found before {action.ex_date} for {action.ticker}"
            )
            return 0

        # Reverse the adjustment by dividing by the factor
        reverse_factor = 1.0 / float(action.adjustment_factor)
        unapplied_count = 0

        for price in prices_to_unapply:
            price.open = Decimal(str(float(price.open) * reverse_factor))
            price.high = Decimal(str(float(price.high) * reverse_factor))
            price.low = Decimal(str(float(price.low) * reverse_factor))
            price.close = Decimal(str(float(price.close) * reverse_factor))

            if price.adjusted_close:
                price.adjusted_close = Decimal(
                    str(float(price.adjusted_close) * reverse_factor)
                )

            price.adjustment_factor = Decimal(
                str(float(price.adjustment_factor) * reverse_factor)
            )

            unapplied_count += 1

        # Mark action as unapplied
        action.is_applied = False
        action.applied_at = None

        self.db.commit()

        logger.info(f"Unapplied action for {unapplied_count} price records")

        return unapplied_count

    def verify_and_apply_action(self, action_id: int) -> int:
        """Verify and apply a corporate action.

        Args:
            action_id: Corporate action ID

        Returns:
            Number of price records adjusted
        """
        action = self.db.query(CorporateAction).filter(
            CorporateAction.id == action_id
        ).first()

        if not action:
            logger.error(f"Action {action_id} not found")
            return 0

        if action.is_verified:
            logger.warning(f"Action {action_id} is already verified")
        else:
            action.is_verified = True
            logger.info(f"Verified action {action_id}")

        if action.is_applied:
            logger.warning(f"Action {action_id} is already applied")
            return 0

        return self._apply_single_action(action)

    def get_unapplied_actions(
        self,
        ticker: Optional[str] = None,
        verified_only: bool = True,
    ) -> List[CorporateAction]:
        """Get list of unapplied corporate actions.

        Args:
            ticker: Optional ticker filter
            verified_only: Only return verified actions

        Returns:
            List of unapplied actions
        """
        query = self.db.query(CorporateAction).filter(
            CorporateAction.is_applied == False  # noqa: E712
        )

        if ticker:
            query = query.filter(CorporateAction.ticker == ticker)

        if verified_only:
            query = query.filter(CorporateAction.is_verified == True)  # noqa: E712

        return query.order_by(CorporateAction.ex_date.desc()).all()

    def get_unverified_actions(
        self,
        ticker: Optional[str] = None,
    ) -> List[CorporateAction]:
        """Get list of unverified corporate actions.

        Args:
            ticker: Optional ticker filter

        Returns:
            List of unverified actions
        """
        query = self.db.query(CorporateAction).filter(
            CorporateAction.is_verified == False  # noqa: E712
        )

        if ticker:
            query = query.filter(CorporateAction.ticker == ticker)

        return query.order_by(CorporateAction.ex_date.desc()).all()
