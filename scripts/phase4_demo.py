"""Phase 4 features demonstration script."""
import asyncio
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.trading.broker_adapter import OrderSide, OrderType, PaperTradingAdapter
from src.core.trading.order_manager import OrderManager
from src.core.trading.position_tracker import PositionTracker
from src.core.trading.risk_manager import RiskLimits, RiskManager
from src.database.connection import get_sync_session
from src.utils.config import get_settings
from src.utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)
settings = get_settings()


async def demo_paper_trading():
    """Demonstrate paper trading."""
    logger.info("=== Paper Trading Demo ===\n")

    # Initialize paper trading broker
    broker = PaperTradingAdapter(initial_cash=Decimal("100000000"))  # 100M VND
    await broker.connect()

    # Create buy order
    logger.info("Creating BUY order for VCB...")
    buy_order = await broker.create_order(
        ticker="VCB",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=1000,
        price=Decimal("95.5"),
    )

    # Submit order
    await broker.submit_order(buy_order)

    logger.info(f"Order Status: {buy_order.status.value}")
    logger.info(f"Filled Quantity: {buy_order.filled_quantity}")
    logger.info(f"Average Fill Price: {buy_order.average_fill_price}\n")

    # Check balance
    balance = await broker.get_account_balance()
    logger.info(f"Account Balance:")
    logger.info(f"  Cash: {balance['cash']:,.2f} VND")
    logger.info(f"  Total Value: {balance['total_value']:,.2f} VND\n")

    # Check positions
    positions = await broker.get_positions()
    logger.info(f"Positions ({len(positions)}):")
    for pos in positions:
        logger.info(f"  {pos['ticker']}: {pos['quantity']} shares @ {pos['average_price']:.2f}")

    await broker.disconnect()
    logger.info("\nPaper trading demo complete\n")


async def demo_risk_management():
    """Demonstrate risk management."""
    logger.info("=== Risk Management Demo ===\n")

    db = next(get_sync_session())

    # Configure risk limits
    risk_limits = RiskLimits(
        max_position_size_pct=0.10,  # 10% max per position
        max_daily_loss_pct=0.02,  # 2% daily loss limit
        max_drawdown_pct=0.10,  # 10% max drawdown
        min_cash_balance_pct=0.05,  # 5% minimum cash
    )

    risk_manager = RiskManager(db, risk_limits)

    logger.info("Risk Limits:")
    logger.info(f"  Max Position Size: {risk_limits.max_position_size_pct:.0%}")
    logger.info(f"  Max Daily Loss: {risk_limits.max_daily_loss_pct:.0%}")
    logger.info(f"  Max Drawdown: {risk_limits.max_drawdown_pct:.0%}")
    logger.info(f"  Min Cash: {risk_limits.min_cash_balance_pct:.0%}\n")

    # Calculate position size
    ticker = "VCB"
    portfolio_value = Decimal("100000000")

    quantity = risk_manager.calculate_position_size(
        ticker,
        portfolio_value,
        volatility=0.02,  # 2% daily volatility
        risk_per_trade_pct=0.01,  # 1% risk per trade
    )

    logger.info(f"Recommended Position Size for {ticker}: {quantity} shares\n")

    # Calculate stop loss
    entry_price = Decimal("95.5")
    stop_loss = risk_manager.calculate_stop_loss(
        ticker,
        entry_price,
        method="fixed_pct",
        fixed_pct=0.05,  # 5% stop
    )

    logger.info(f"Entry Price: {entry_price:.2f}")
    logger.info(f"Stop Loss: {stop_loss:.2f} ({(stop_loss/entry_price - 1):.2%})")

    # Calculate take profit
    take_profit = risk_manager.calculate_take_profit(
        entry_price,
        stop_loss,
        risk_reward_ratio=2.0,
    )

    logger.info(f"Take Profit: {take_profit:.2f} ({(take_profit/entry_price - 1):.2%})\n")

    # Generate risk report
    positions = {
        "VCB": {"quantity": 1000, "current_price": 98.0},
        "VHM": {"quantity": 500, "current_price": 75.0},
    }

    report = risk_manager.generate_risk_report(
        portfolio_value,
        Decimal("20000000"),  # 20M cash
        positions,
    )

    logger.info("Risk Report:")
    logger.info(f"  Portfolio Value: {report['portfolio_value']:,.2f}")
    logger.info(f"  Cash: {report['cash_percentage']:.1%}")
    logger.info(f"  Positions: {report['number_of_positions']}")
    logger.info(f"  Largest Position: {report['largest_position']['ticker']} ({report['largest_position']['percentage']:.1%})")
    logger.info(f"  VaR (95%, 1d): {report['var_95_1day']:,.2f}")

    db.close()
    logger.info("\nRisk management demo complete\n")


async def demo_order_management():
    """Demonstrate order management."""
    logger.info("=== Order Management Demo ===\n")

    db = next(get_sync_session())

    # Setup
    broker = PaperTradingAdapter(initial_cash=Decimal("100000000"))
    await broker.connect()

    risk_manager = RiskManager(db)
    order_manager = OrderManager(db, broker, risk_manager)

    # Create market order
    logger.info("Creating market orders...")
    buy_order = await order_manager.create_market_order(
        ticker="VCB",
        side=OrderSide.BUY,
        quantity=1000,
        submit=True,
    )

    logger.info(f"Market Order Created: {buy_order.order_id}")
    logger.info(f"Status: {buy_order.status.value}\n")

    # Create limit order
    logger.info("Creating limit order...")
    limit_order = await order_manager.create_limit_order(
        ticker="VHM",
        side=OrderSide.BUY,
        quantity=500,
        price=Decimal("75.0"),
        submit=True,
    )

    logger.info(f"Limit Order Created: {limit_order.order_id}")
    logger.info(f"Status: {limit_order.status.value}\n")

    # Get order summary
    summary = order_manager.get_order_summary()
    logger.info("Order Summary:")
    logger.info(f"  Total Orders: {summary['total_orders']}")
    logger.info(f"  Filled: {summary['filled']}")
    logger.info(f"  Pending: {summary['pending']}")
    logger.info(f"  Cancelled: {summary['cancelled']}\n")

    # Get filled orders
    filled = order_manager.get_filled_orders()
    logger.info(f"Filled Orders ({len(filled)}):")
    for order in filled:
        logger.info(
            f"  {order.ticker}: {order.side.value} {order.quantity} @ "
            f"{order.average_fill_price if order.average_fill_price else 'N/A'}"
        )

    await broker.disconnect()
    db.close()
    logger.info("\nOrder management demo complete\n")


async def demo_position_tracking():
    """Demonstrate position tracking."""
    logger.info("=== Position Tracking Demo ===\n")

    db = next(get_sync_session())

    # Setup with paper trading
    broker = PaperTradingAdapter(initial_cash=Decimal("100000000"))
    await broker.connect()

    # Create some positions
    await broker.buy("VCB", date.today(), Decimal("95.5"), 1000)
    await broker.buy("VHM", date.today(), Decimal("75.0"), 500)
    await broker.buy("VIC", date.today(), Decimal("42.5"), 2000)

    # Initialize position tracker
    tracker = PositionTracker(db, broker)

    # Sync with broker
    await tracker.sync_with_broker()

    logger.info("Portfolio Summary:")
    summary = tracker.get_portfolio_summary()
    logger.info(f"  Total Value: {summary['total_value']:,.2f} VND")
    logger.info(f"  Cash: {summary['cash']:,.2f} VND ({summary['cash_pct']:.1%})")
    logger.info(f"  Positions Value: {summary['positions_value']:,.2f} VND")
    logger.info(f"  Number of Positions: {summary['number_of_positions']}")
    logger.info(f"  Total Unrealized P&L: {summary['total_unrealized_pnl']:,.2f} VND ({summary['total_unrealized_pnl_pct']:.2%})\n")

    # Position breakdown
    logger.info("Position Breakdown:")
    breakdown = tracker.get_position_breakdown()
    for pos in breakdown:
        logger.info(
            f"  {pos['ticker']}: {pos['quantity']} shares @ {pos['average_price']:.2f} "
            f"(Current: {pos['current_price']:.2f}, P&L: {pos['unrealized_pnl']:,.2f}, "
            f"{pos['unrealized_pnl_pct']:+.2%}, Weight: {pos['weight']:.1%})"
        )

    logger.info("")

    # Top performers
    top = tracker.get_top_performers(limit=3)
    logger.info("Top Performers:")
    for pos in top:
        logger.info(f"  {pos['ticker']}: {pos['unrealized_pnl_pct']:+.2%}")

    await broker.disconnect()
    db.close()
    logger.info("\nPosition tracking demo complete\n")


async def demo_integrated_trading_workflow():
    """Demonstrate integrated trading workflow."""
    logger.info("=== Integrated Trading Workflow Demo ===\n")

    db = next(get_sync_session())

    # 1. Setup
    logger.info("Step 1: Setting up trading system...")
    broker = PaperTradingAdapter(initial_cash=Decimal("100000000"))
    await broker.connect()

    risk_manager = RiskManager(db, RiskLimits())
    order_manager = OrderManager(db, broker, risk_manager)
    position_tracker = PositionTracker(db, broker)

    logger.info("  ✓ Broker connected")
    logger.info("  ✓ Risk manager initialized")
    logger.info("  ✓ Order manager ready")
    logger.info("  ✓ Position tracker ready\n")

    # 2. Analyze & Calculate Position Size
    logger.info("Step 2: Analyzing VCB...")
    ticker = "VCB"
    portfolio_value = Decimal("100000000")

    quantity = risk_manager.calculate_position_size(
        ticker,
        portfolio_value,
        risk_per_trade_pct=0.01,
    )

    logger.info(f"  Recommended quantity: {quantity} shares\n")

    # 3. Create Order with Risk Management
    logger.info("Step 3: Creating order with risk checks...")
    entry_price = Decimal("95.5")

    order = await order_manager.create_limit_order(
        ticker=ticker,
        side=OrderSide.BUY,
        quantity=quantity,
        price=entry_price,
        submit=True,  # Automatically validates risk
    )

    logger.info(f"  Order status: {order.status.value}\n")

    # 4. Set Stop Loss & Take Profit
    logger.info("Step 4: Setting stop loss and take profit...")
    stop_loss = risk_manager.calculate_stop_loss(ticker, entry_price)
    take_profit = risk_manager.calculate_take_profit(entry_price, stop_loss)

    logger.info(f"  Entry: {entry_price:.2f}")
    logger.info(f"  Stop Loss: {stop_loss:.2f} ({(stop_loss/entry_price - 1):.2%})")
    logger.info(f"  Take Profit: {take_profit:.2f} ({(take_profit/entry_price - 1):.2%})\n")

    # 5. Monitor Position
    logger.info("Step 5: Monitoring position...")
    await position_tracker.sync_with_broker()

    position = position_tracker.get_position(ticker)
    if position:
        logger.info(f"  Position: {position.quantity} shares")
        logger.info(f"  Average Price: {position.average_price:.2f}")
        logger.info(f"  Unrealized P&L: {position.unrealized_pnl:,.2f} ({position.unrealized_pnl_pct:+.2%})\n")

    # 6. Risk Report
    logger.info("Step 6: Generating risk report...")
    balance = await broker.get_account_balance()
    positions_dict = {
        pos["ticker"]: pos
        for pos in await broker.get_positions()
    }

    report = risk_manager.generate_risk_report(
        Decimal(str(balance["total_value"])),
        Decimal(str(balance["cash"])),
        positions_dict,
    )

    logger.info(f"  Portfolio Value: {report['portfolio_value']:,.2f}")
    logger.info(f"  Positions: {report['number_of_positions']}")
    logger.info(f"  Cash: {report['cash_percentage']:.1%}")

    await broker.disconnect()
    db.close()
    logger.info("\nIntegrated workflow demo complete\n")


def main():
    """Run all Phase 4 demos."""
    logger.info("Starting Phase 4 Features Demonstration\n")
    logger.info("=" * 60 + "\n")

    try:
        # Demo 1: Paper Trading
        asyncio.run(demo_paper_trading())

        # Demo 2: Risk Management
        asyncio.run(demo_risk_management())

        # Demo 3: Order Management
        asyncio.run(demo_order_management())

        # Demo 4: Position Tracking
        asyncio.run(demo_position_tracking())

        # Demo 5: Integrated Workflow
        asyncio.run(demo_integrated_trading_workflow())

        logger.info("=" * 60)
        logger.info("All Phase 4 demos completed successfully! 🎉")

    except Exception as e:
        logger.error(f"Demo error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
