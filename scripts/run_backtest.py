"""
Backtest Script - Công cụ backtest chiến lược giao dịch

Cách sử dụng:
    python scripts/run_backtest.py --help
    python scripts/run_backtest.py --strategy ma --tickers VCB,VNM,HPG
    python scripts/run_backtest.py --compare --tickers VCB,VNM,HPG,VIC,MSN
    python scripts/run_backtest.py --custom my_strategy.py

Tính năng:
    - Backtest với nhiều chiến lược có sẵn
    - So sánh hiệu quả các chiến lược
    - Tạo báo cáo chi tiết và biểu đồ
    - Hỗ trợ chiến lược tùy chỉnh
    - Xuất kết quả ra CSV/JSON
"""

import argparse
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Callable
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend

from src.core.backtesting.engine import BacktestEngine
from src.core.backtesting.strategies import (
    simple_moving_average_strategy,
    momentum_strategy,
    mean_reversion_strategy,
    buy_and_hold_strategy
)
from src.database.connection import get_sync_session
from src.utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


class BacktestRunner:
    """Quản lý việc chạy backtest và tạo báo cáo."""

    def __init__(
        self,
        initial_capital: float = 100_000_000,
        commission_rate: float = 0.0015,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ):
        """
        Khởi tạo BacktestRunner.

        Args:
            initial_capital: Vốn ban đầu (VND)
            commission_rate: Phí giao dịch (%)
            start_date: Ngày bắt đầu backtest
            end_date: Ngày kết thúc backtest
        """
        self.db = next(get_sync_session())
        self.engine = BacktestEngine(
            self.db,
            initial_capital=Decimal(str(initial_capital)),
            commission_rate=commission_rate
        )

        self.end_date = end_date or date.today()
        self.start_date = start_date or (self.end_date - timedelta(days=365))

        logger.info(f"BacktestRunner initialized: {self.start_date} to {self.end_date}")

    def run_single_strategy(
        self,
        strategy_name: str,
        tickers: List[str],
        params: Optional[Dict] = None
    ) -> Dict:
        """
        Chạy backtest với một chiến lược.

        Args:
            strategy_name: Tên chiến lược (ma, momentum, mean_reversion, buy_hold)
            tickers: Danh sách mã cổ phiếu
            params: Tham số chiến lược

        Returns:
            Kết quả backtest
        """
        params = params or {}
        strategy_func = self._get_strategy_function(strategy_name, params)

        if not strategy_func:
            raise ValueError(f"Chiến lược '{strategy_name}' không tồn tại")

        logger.info(f"Đang chạy backtest cho chiến lược: {strategy_name}")
        logger.info(f"Mã cổ phiếu: {', '.join(tickers)}")
        logger.info(f"Thời gian: {self.start_date} → {self.end_date}")

        results = self.engine.run(
            strategy=strategy_func,
            tickers=tickers,
            start_date=self.start_date,
            end_date=self.end_date
        )

        if results:
            results['strategy_name'] = strategy_name
            results['strategy_params'] = params
            results['tickers'] = tickers

        return results

    def compare_strategies(
        self,
        tickers: List[str],
        strategies: Optional[List[str]] = None
    ) -> Dict[str, Dict]:
        """
        So sánh nhiều chiến lược.

        Args:
            tickers: Danh sách mã cổ phiếu
            strategies: Danh sách tên chiến lược (None = tất cả)

        Returns:
            Dict[strategy_name, results]
        """
        if strategies is None:
            strategies = ["ma", "momentum", "mean_reversion", "buy_hold"]

        logger.info(f"So sánh {len(strategies)} chiến lược")

        comparison = {}

        for strategy_name in strategies:
            try:
                # Reset engine for each strategy
                self.engine = BacktestEngine(
                    self.db,
                    initial_capital=self.engine.initial_capital,
                    commission_rate=self.engine.commission_rate
                )

                results = self.run_single_strategy(strategy_name, tickers)

                # Check if results are valid
                if not results or 'total_return' not in results:
                    error_msg = f"No price data for {', '.join(tickers)} in date range {self.start_date} to {self.end_date}"
                    logger.error(f"✗ {strategy_name}: {error_msg}")
                    comparison[strategy_name] = {"error": error_msg}
                else:
                    comparison[strategy_name] = results
                    logger.info(f"✓ {strategy_name}: {results['total_return']:.2%}")

            except Exception as e:
                logger.error(f"✗ {strategy_name}: {e}")
                comparison[strategy_name] = {"error": str(e)}

        return comparison

    def _get_strategy_function(
        self,
        name: str,
        params: Dict
    ) -> Optional[Callable]:
        """Lấy hàm chiến lược từ tên."""

        strategies = {
            "ma": lambda d, p, c: simple_moving_average_strategy(
                d, p, c,
                short_window=params.get("short_window", 20),
                long_window=params.get("long_window", 50)
            ),
            "momentum": lambda d, p, c: momentum_strategy(
                d, p, c,
                lookback=params.get("lookback", 20),
                top_n=params.get("top_n", 5)
            ),
            "mean_reversion": lambda d, p, c: mean_reversion_strategy(
                d, p, c,
                window=params.get("window", 20),
                std_threshold=params.get("std_threshold", 2.0)
            ),
            "buy_hold": buy_and_hold_strategy
        }

        return strategies.get(name)

    def print_results(self, results: Dict) -> None:
        """In kết quả backtest ra console."""

        if not results or "error" in results:
            logger.error(f"Không có kết quả hoặc có lỗi: {results.get('error', 'Unknown')}")
            return

        print("\n" + "="*70)
        print(f"KẾT QUẢ BACKTEST - {results.get('strategy_name', 'Unknown').upper()}")
        print("="*70)

        print(f"\nThời gian: {self.start_date} → {self.end_date}")
        print(f"Mã CP: {', '.join(results.get('tickers', []))}")

        params = results.get('strategy_params', {})
        if params:
            print(f"Tham số: {params}")

        print("\n--- TỔNG QUAN ---")
        print(f"Vốn ban đầu:     {results['initial_capital']:>15,.0f} VND")
        print(f"Giá trị cuối:    {results['final_value']:>15,.0f} VND")
        print(f"Lợi nhuận:       {results['total_return']:>15.2%}")

        profit_loss = results['final_value'] - results['initial_capital']
        print(f"P&L:             {profit_loss:>15,.0f} VND")

        stats = results.get('statistics', {})
        if stats:
            print("\n--- THỐNG KÊ GIAO DỊCH ---")
            print(f"Tổng giao dịch:  {stats['total_trades']:>15}")
            print(f"Thắng:           {stats['winning_trades']:>15}")
            print(f"Thua:            {stats['losing_trades']:>15}")
            print(f"Tỷ lệ thắng:     {stats['win_rate']:>15.2%}")
            print(f"P&L trung bình:  {stats['avg_pnl']:>15,.0f} VND")
            print(f"P&L TB (%):      {stats['total_pnl_pct']:>15.2%}")
            print(f"Thắng TB:        {stats['avg_win']:>15,.0f} VND")
            print(f"Thua TB:         {stats['avg_loss']:>15,.0f} VND")
            print(f"Profit Factor:   {stats['profit_factor']:>15.2f}")

        trades = results.get('trades', [])
        if trades:
            print(f"\n--- CHI TIẾT {min(10, len(trades))} GIAO DỊCH ĐẦU TIÊN ---")
            print(f"{'Mã':>5} | {'Vào':>10} | {'Giá vào':>10} | {'Ra':>10} | {'Giá ra':>10} | {'P&L':>12} | {'%':>8}")
            print("-" * 80)

            for trade in trades[:10]:
                pnl = trade.get('pnl', 0) or 0
                pnl_pct = trade.get('pnl_pct', 0) or 0

                print(f"{trade['ticker']:>5} | "
                      f"{str(trade['entry_date']):>10} | "
                      f"{trade['entry_price']:>10.2f} | "
                      f"{str(trade['exit_date']):>10} | "
                      f"{trade['exit_price'] if trade['exit_price'] else 0:>10.2f} | "
                      f"{pnl:>12,.0f} | "
                      f"{pnl_pct:>7.2%}")

        print("\n" + "="*70 + "\n")

    def print_comparison(self, comparison: Dict[str, Dict]) -> None:
        """In bảng so sánh các chiến lược."""

        print("\n" + "="*100)
        print("SO SÁNH CHIẾN LƯỢC")
        print("="*100)

        print(f"\n{'Chiến lược':<20} | {'Lợi nhuận':>12} | {'P&L':>15} | "
              f"{'Giao dịch':>10} | {'Tỷ lệ thắng':>12} | {'Profit Factor':>14}")
        print("-" * 100)

        for name, results in comparison.items():
            if "error" in results:
                print(f"{name:<20} | ERROR: {results['error']}")
                continue

            stats = results.get('statistics', {})
            pnl = results['final_value'] - results['initial_capital']

            print(f"{name:<20} | "
                  f"{results['total_return']:>11.2%} | "
                  f"{pnl:>14,.0f} | "
                  f"{stats.get('total_trades', 0):>10} | "
                  f"{stats.get('win_rate', 0):>11.2%} | "
                  f"{stats.get('profit_factor', 0):>14.2f}")

        # Tìm chiến lược tốt nhất
        best_strategy = max(
            [(name, r) for name, r in comparison.items() if "error" not in r],
            key=lambda x: x[1].get('total_return', -999),
            default=(None, None)
        )

        if best_strategy[0]:
            print(f"\n🏆 Chiến lược tốt nhất: {best_strategy[0].upper()} "
                  f"({best_strategy[1]['total_return']:.2%})")

        print("\n" + "="*100 + "\n")

    def save_results(
        self,
        results: Dict,
        output_dir: str = "backtest_results"
    ) -> None:
        """Lưu kết quả backtest."""

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        timestamp = date.today().strftime("%Y%m%d")
        strategy_name = results.get('strategy_name', 'unknown')

        # Save JSON
        json_file = output_path / f"{strategy_name}_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            # Convert Decimal to float for JSON serialization
            results_copy = self._prepare_for_json(results)
            json.dump(results_copy, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Đã lưu kết quả JSON: {json_file}")

        # Save trades to CSV
        trades = results.get('trades', [])
        if trades:
            csv_file = output_path / f"{strategy_name}_{timestamp}_trades.csv"
            df = pd.DataFrame(trades)
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            logger.info(f"Đã lưu giao dịch CSV: {csv_file}")

        # Save equity curve to CSV
        equity_curve = results.get('equity_curve', [])
        if equity_curve:
            eq_file = output_path / f"{strategy_name}_{timestamp}_equity.csv"
            df_eq = pd.DataFrame(equity_curve)
            df_eq.to_csv(eq_file, index=False, encoding='utf-8-sig')
            logger.info(f"Đã lưu equity curve: {eq_file}")

    def _prepare_for_json(self, obj):
        """Chuẩn bị object cho JSON serialization."""
        if isinstance(obj, dict):
            return {k: self._prepare_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._prepare_for_json(item) for item in obj]
        elif isinstance(obj, (Decimal, float)):
            return float(obj)
        elif isinstance(obj, (date,)):
            return str(obj)
        return obj

    def plot_equity_curve(
        self,
        results: Dict,
        output_dir: str = "backtest_results"
    ) -> None:
        """Vẽ biểu đồ equity curve."""

        equity_curve = results.get('equity_curve', [])
        if not equity_curve:
            logger.warning("Không có dữ liệu equity curve để vẽ")
            return

        df = pd.DataFrame(equity_curve)
        df['date'] = pd.to_datetime(df['date'])

        plt.figure(figsize=(14, 8))

        # Plot 1: Portfolio Value
        plt.subplot(2, 1, 1)
        plt.plot(df['date'], df['value'], linewidth=2, label='Portfolio Value')
        plt.axhline(
            y=results['initial_capital'],
            color='r',
            linestyle='--',
            alpha=0.5,
            label='Initial Capital'
        )
        plt.title(
            f"Equity Curve - {results.get('strategy_name', 'Unknown').upper()}\n"
            f"Return: {results['total_return']:.2%}",
            fontsize=14,
            fontweight='bold'
        )
        plt.xlabel('Date')
        plt.ylabel('Portfolio Value (VND)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.ticklabel_format(style='plain', axis='y')

        # Plot 2: Cash vs Positions
        plt.subplot(2, 1, 2)
        plt.plot(df['date'], df['cash'], label='Cash', linewidth=2)
        plt.plot(
            df['date'],
            df['value'] - df['cash'],
            label='Position Value',
            linewidth=2
        )
        plt.title('Cash vs Position Value', fontsize=12)
        plt.xlabel('Date')
        plt.ylabel('Value (VND)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.ticklabel_format(style='plain', axis='y')

        plt.tight_layout()

        # Save plot
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        timestamp = date.today().strftime("%Y%m%d")
        strategy_name = results.get('strategy_name', 'unknown')
        plot_file = output_path / f"{strategy_name}_{timestamp}_equity.png"

        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        logger.info(f"Đã lưu biểu đồ: {plot_file}")

        plt.close()

    def plot_comparison(
        self,
        comparison: Dict[str, Dict],
        output_dir: str = "backtest_results"
    ) -> None:
        """Vẽ biểu đồ so sánh các chiến lược."""

        valid_results = {
            name: results for name, results in comparison.items()
            if "error" not in results and results.get('equity_curve')
        }

        if not valid_results:
            logger.warning("Không có dữ liệu hợp lệ để vẽ so sánh")
            return

        plt.figure(figsize=(14, 10))

        # Plot 1: Equity Curves
        plt.subplot(2, 2, 1)
        for name, results in valid_results.items():
            df = pd.DataFrame(results['equity_curve'])
            df['date'] = pd.to_datetime(df['date'])
            plt.plot(df['date'], df['value'], label=name.upper(), linewidth=2)

        plt.title('Equity Curves Comparison', fontsize=12, fontweight='bold')
        plt.xlabel('Date')
        plt.ylabel('Portfolio Value (VND)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.ticklabel_format(style='plain', axis='y')

        # Plot 2: Returns Bar Chart
        plt.subplot(2, 2, 2)
        names = list(valid_results.keys())
        returns = [r['total_return'] * 100 for r in valid_results.values()]
        colors = ['green' if r > 0 else 'red' for r in returns]

        plt.bar(names, returns, color=colors, alpha=0.7)
        plt.title('Total Returns Comparison', fontsize=12, fontweight='bold')
        plt.xlabel('Strategy')
        plt.ylabel('Return (%)')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3, axis='y')

        # Plot 3: Win Rate
        plt.subplot(2, 2, 3)
        win_rates = [
            r['statistics'].get('win_rate', 0) * 100
            for r in valid_results.values()
        ]
        plt.bar(names, win_rates, color='blue', alpha=0.7)
        plt.title('Win Rate Comparison', fontsize=12, fontweight='bold')
        plt.xlabel('Strategy')
        plt.ylabel('Win Rate (%)')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3, axis='y')
        plt.ylim(0, 100)

        # Plot 4: Number of Trades
        plt.subplot(2, 2, 4)
        trades = [
            r['statistics'].get('total_trades', 0)
            for r in valid_results.values()
        ]
        plt.bar(names, trades, color='orange', alpha=0.7)
        plt.title('Total Trades Comparison', fontsize=12, fontweight='bold')
        plt.xlabel('Strategy')
        plt.ylabel('Number of Trades')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()

        # Save plot
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        timestamp = date.today().strftime("%Y%m%d")
        plot_file = output_path / f"comparison_{timestamp}.png"

        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        logger.info(f"Đã lưu biểu đồ so sánh: {plot_file}")

        plt.close()

    def close(self):
        """Đóng kết nối database."""
        self.db.close()


def main():
    """Main function."""

    parser = argparse.ArgumentParser(
        description="Backtest Tool - Công cụ backtest chiến lược giao dịch",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ sử dụng:
  # Backtest chiến lược Moving Average
  python scripts/run_backtest.py --strategy ma --tickers VCB,VNM,HPG

  # Backtest với tham số tùy chỉnh
  python scripts/run_backtest.py --strategy ma --tickers VCB,VNM --short-window 10 --long-window 30

  # So sánh tất cả các chiến lược
  python scripts/run_backtest.py --compare --tickers VCB,VNM,HPG,VIC,MSN

  # Backtest với thời gian cụ thể
  python scripts/run_backtest.py --strategy momentum --tickers VCB,VNM --start-date 2023-01-01 --end-date 2024-12-31

  # Lưu kết quả và tạo biểu đồ
  python scripts/run_backtest.py --strategy ma --tickers VCB,VNM,HPG --save --plot
        """
    )

    # Basic arguments
    parser.add_argument(
        "--tickers",
        type=str,
        required=True,
        help="Danh sách mã cổ phiếu (phân cách bằng dấu phẩy). VD: VCB,VNM,HPG"
    )

    parser.add_argument(
        "--strategy",
        type=str,
        choices=["ma", "momentum", "mean_reversion", "buy_hold"],
        help="Chiến lược giao dịch: ma (Moving Average), momentum, mean_reversion, buy_hold"
    )

    parser.add_argument(
        "--compare",
        action="store_true",
        help="So sánh tất cả các chiến lược"
    )

    # Time range
    parser.add_argument(
        "--start-date",
        type=str,
        help="Ngày bắt đầu (YYYY-MM-DD). Mặc định: 1 năm trước"
    )

    parser.add_argument(
        "--end-date",
        type=str,
        help="Ngày kết thúc (YYYY-MM-DD). Mặc định: hôm nay"
    )

    # Capital and commission
    parser.add_argument(
        "--capital",
        type=float,
        default=100_000_000,
        help="Vốn ban đầu (VND). Mặc định: 100,000,000"
    )

    parser.add_argument(
        "--commission",
        type=float,
        default=0.0015,
        help="Phí giao dịch (%%/100). Mặc định: 0.0015 (0.15%%)"
    )

    # Strategy parameters - MA
    parser.add_argument(
        "--short-window",
        type=int,
        default=20,
        help="MA ngắn hạn (ngày). Mặc định: 20"
    )

    parser.add_argument(
        "--long-window",
        type=int,
        default=50,
        help="MA dài hạn (ngày). Mặc định: 50"
    )

    # Strategy parameters - Momentum
    parser.add_argument(
        "--lookback",
        type=int,
        default=20,
        help="Kỳ nhìn lại cho momentum (ngày). Mặc định: 20"
    )

    parser.add_argument(
        "--top-n",
        type=int,
        default=5,
        help="Số lượng cổ phiếu giữ trong momentum. Mặc định: 5"
    )

    # Strategy parameters - Mean Reversion
    parser.add_argument(
        "--window",
        type=int,
        default=20,
        help="Kỳ tính Bollinger Bands (ngày). Mặc định: 20"
    )

    parser.add_argument(
        "--std-threshold",
        type=float,
        default=2.0,
        help="Số độ lệch chuẩn cho Bollinger Bands. Mặc định: 2.0"
    )

    # Output options
    parser.add_argument(
        "--save",
        action="store_true",
        help="Lưu kết quả ra file"
    )

    parser.add_argument(
        "--plot",
        action="store_true",
        help="Tạo biểu đồ"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="backtest_results",
        help="Thư mục lưu kết quả. Mặc định: backtest_results"
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.compare and not args.strategy:
        parser.error("Cần chỉ định --strategy hoặc --compare")

    # Parse dates
    start_date = None
    end_date = None

    if args.start_date:
        try:
            start_date = date.fromisoformat(args.start_date)
        except ValueError:
            logger.error(f"Ngày bắt đầu không hợp lệ: {args.start_date}")
            sys.exit(1)

    if args.end_date:
        try:
            end_date = date.fromisoformat(args.end_date)
        except ValueError:
            logger.error(f"Ngày kết thúc không hợp lệ: {args.end_date}")
            sys.exit(1)

    # Parse tickers
    tickers = [t.strip().upper() for t in args.tickers.split(',')]

    # Initialize runner
    runner = BacktestRunner(
        initial_capital=args.capital,
        commission_rate=args.commission,
        start_date=start_date,
        end_date=end_date
    )

    try:
        if args.compare:
            # Compare all strategies
            logger.info("Chế độ so sánh chiến lược")
            comparison = runner.compare_strategies(tickers)
            runner.print_comparison(comparison)

            if args.plot:
                runner.plot_comparison(comparison, args.output_dir)

            if args.save:
                for name, results in comparison.items():
                    if "error" not in results:
                        runner.save_results(results, args.output_dir)

        else:
            # Single strategy backtest
            params = {
                "short_window": args.short_window,
                "long_window": args.long_window,
                "lookback": args.lookback,
                "top_n": args.top_n,
                "window": args.window,
                "std_threshold": args.std_threshold
            }

            results = runner.run_single_strategy(
                args.strategy,
                tickers,
                params
            )

            if not results or 'total_return' not in results:
                logger.error(
                    f"Không có dữ liệu giá cho {', '.join(tickers)} "
                    f"trong khoảng thời gian {runner.start_date} đến {runner.end_date}"
                )
                logger.info("Gợi ý: Hãy kiểm tra lại mã cổ phiếu và khoảng thời gian, hoặc tải dữ liệu bằng lệnh: make load-stocks")
                sys.exit(1)

            runner.print_results(results)

            if args.plot:
                runner.plot_equity_curve(results, args.output_dir)

            if args.save:
                runner.save_results(results, args.output_dir)

        logger.info("✅ Hoàn thành!")

    except Exception as e:
        logger.error(f"Lỗi: {e}", exc_info=True)
        sys.exit(1)

    finally:
        runner.close()


if __name__ == "__main__":
    main()
