"""
Quant Module

Provides quantitative analysis tools including indicators, factors, quotes, and backtesting.
Based on Mai-language syntax compatible with TongDaXin/TongHuaShun.
"""

from typing import Any, Literal

import pandas as pd


StockMarket = Literal["cn", "hk", "us"]


class QuantModule:
    """
    Quantitative analysis module

    Access technical indicators, factors, OHLCV quotes, and backtesting functionality.
    Uses Mai-language syntax for formulas.

    Example:
        >>> quant = client.quant
        >>> # Compute RSI indicator
        >>> df = quant.compute_indicators(["000001"], "RSI(14)")
        >>> # Screen stocks by formula
        >>> stocks = quant.screen(formula="RSI(14) < 30")
    """

    def __init__(self, client):
        self._client = client

    # -------------------------------------------------------------------------
    # Indicators
    # -------------------------------------------------------------------------

    def list_indicators(self) -> list[dict[str, Any]]:
        """
        Get list of available technical indicators

        Returns:
            List of indicator definitions with name, description, and fields

        Example:
            >>> indicators = client.quant.list_indicators()
            >>> for ind in indicators:
            ...     print(f"{ind['name']}: {ind['description']}")
            ...     print(f"  Fields: {ind['fields']}")
        """
        return self._client._get("/v1/quant/indicators")

    def compute_indicators(
        self,
        symbols: list[str],
        formula: str,
        *,
        market: StockMarket = "cn",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """
        Compute indicator values for given symbols

        Args:
            symbols: List of stock codes (e.g., ["000001", "600519"])
            formula: Indicator formula (e.g., "RSI(14)", "MACD()", "MACD(12,26,9)")
            market: Stock market ("cn", "hk", "us"), default "cn"
            start_date: Start date (YYYY-MM-DD), default 3 months ago
            end_date: End date (YYYY-MM-DD), default today

        Returns:
            DataFrame with indicator values

        Example:
            >>> # RSI indicator
            >>> df = client.quant.compute_indicators(["000001"], "RSI(14)")
            >>> print(df[["symbol", "date", "rsi"]])
            
            >>> # MACD indicator
            >>> df = client.quant.compute_indicators(["000001"], "MACD()")
            >>> print(df[["symbol", "date", "dif", "dea", "macd"]])
            
            >>> # KDJ indicator
            >>> df = client.quant.compute_indicators(["000001"], "KDJ(9,3,3)")
            >>> print(df[["symbol", "date", "k", "d", "j"]])
        """
        data: dict[str, Any] = {
            "symbols": symbols,
            "formula": formula,
            "market": market,
        }
        if start_date:
            data["start_date"] = start_date
        if end_date:
            data["end_date"] = end_date

        response = self._client._post("/v1/quant/indicators/compute", json=data)
        return self._to_dataframe(response.get("datas", []))

    # -------------------------------------------------------------------------
    # Factors
    # -------------------------------------------------------------------------

    def list_factors(self) -> list[dict[str, Any]]:
        """
        Get list of available factors (variables and functions)

        Returns factors organized by level:
        - Level 0 Variables: CLOSE, OPEN, HIGH, LOW, VOLUME
        - Level 0 Functions: MA, EMA, REF, HHV, LLV, STD, etc.
        - Level 1 Functions: CROSS, COUNT, EVERY, etc.
        - Level 2 Functions: MACD, KDJ, RSI, BOLL, etc.

        Returns:
            List of factor definitions

        Example:
            >>> factors = client.quant.list_factors()
            >>> for f in factors:
            ...     print(f"{f['name']} ({f['type']}, level {f['level']})")
        """
        return self._client._get("/v1/quant/factors")

    def compute_factors(
        self,
        symbols: list[str],
        formula: str,
        *,
        market: StockMarket = "cn",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """
        Compute factor values for given symbols

        Uses Mai-language syntax compatible with TongDaXin/TongHuaShun.

        Args:
            symbols: List of stock codes
            formula: Factor formula using Mai-language syntax
            market: Stock market ("cn", "hk", "us"), default "cn"
            start_date: Start date (YYYY-MM-DD), default 3 months ago
            end_date: End date (YYYY-MM-DD), default today

        Returns:
            DataFrame with factor values

        Example:
            >>> # Simple indicator
            >>> df = client.quant.compute_factors(["000001"], "RSI(14)")
            
            >>> # MACD DIF line
            >>> df = client.quant.compute_factors(["000001"], "MACD().dif")
            
            >>> # Close above 20-day MA (boolean)
            >>> df = client.quant.compute_factors(["000001"], "CLOSE > MA(20)")
            
            >>> # Deviation from MA20 in percent
            >>> df = client.quant.compute_factors(["000001"], "(CLOSE - MA(20)) / MA(20) * 100")

        Supported Operators:
            - Comparison: >, <, >=, <=, ==, !=
            - Logical AND: & (NOT "AND")
            - Logical OR: | (NOT "OR")
            - Arithmetic: +, -, *, /

        Supported Variables:
            - CLOSE, C: Close price
            - OPEN, O: Open price
            - HIGH, H: High price
            - LOW, L: Low price
            - VOLUME, V, VOL: Volume
        """
        data: dict[str, Any] = {
            "symbols": symbols,
            "formula": formula,
            "market": market,
        }
        if start_date:
            data["start_date"] = start_date
        if end_date:
            data["end_date"] = end_date

        response = self._client._post("/v1/quant/factors/compute", json=data)
        return self._to_dataframe(response.get("datas", []))

    def screen(
        self,
        formula: str,
        *,
        market: StockMarket = "cn",
        check_date: str | None = None,
        symbols: list[str] | None = None,
    ) -> pd.DataFrame:
        """
        Screen stocks based on factor formula

        Returns stocks where the formula evaluates to True (for boolean formulas)
        or non-null (for numeric formulas).

        Args:
            formula: Screening formula using Mai-language syntax
            market: Stock market ("cn", "hk", "us"), default "cn"
            check_date: Check date (YYYY-MM-DD), default latest trading day
            symbols: Stock codes to screen (None = full market)

        Returns:
            DataFrame with stocks that passed the filter

        Example:
            >>> # RSI oversold
            >>> stocks = client.quant.screen(formula="RSI(14) < 30")
            
            >>> # Golden cross
            >>> stocks = client.quant.screen(formula="CROSS(MA(5), MA(10))")
            
            >>> # Uptrend
            >>> stocks = client.quant.screen(formula="(CLOSE > MA(20)) & (MA(20) > MA(60))")
            
            >>> # Above upper Bollinger Band
            >>> stocks = client.quant.screen(formula="CLOSE > BOLL(20, 2).upper")
            
            >>> # Screen specific stocks
            >>> stocks = client.quant.screen(
            ...     formula="RSI(14) < 30",
            ...     symbols=["000001", "600519", "000002"]
            ... )
        """
        data: dict[str, Any] = {
            "formula": formula,
            "market": market,
        }
        if check_date:
            data["check_date"] = check_date
        if symbols:
            data["symbols"] = symbols

        response = self._client._post("/v1/quant/factors/screen", json=data)
        return self._to_dataframe(response.get("datas", []))

    # -------------------------------------------------------------------------
    # Quotes
    # -------------------------------------------------------------------------

    def ohlcv(
        self,
        symbol: str,
        *,
        market: StockMarket = "cn",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """
        Get OHLCV (Open, High, Low, Close, Volume) daily data for a single symbol

        Args:
            symbol: Stock code
            market: Stock market ("cn", "hk", "us"), default "cn"
            start_date: Start date (YYYY-MM-DD), default 1 month ago
            end_date: End date (YYYY-MM-DD), default today

        Returns:
            DataFrame with OHLCV data

        Example:
            >>> df = client.quant.ohlcv("000001")
            >>> print(df[["open", "high", "low", "close", "volume"]])
        """
        params: dict[str, Any] = {
            "symbol": symbol,
            "market": market,
        }
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        response = self._client._get("/v1/quant/quotes/ohlcv", params=params)
        return self._to_dataframe(response.get("datas", []))

    def ohlcv_batch(
        self,
        symbols: list[str],
        *,
        market: StockMarket = "cn",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """
        Get OHLCV data for multiple symbols

        Args:
            symbols: List of stock codes
            market: Stock market ("cn", "hk", "us"), default "cn"
            start_date: Start date (YYYY-MM-DD), default 1 month ago
            end_date: End date (YYYY-MM-DD), default today

        Returns:
            DataFrame with OHLCV data sorted by date (descending), then by symbol

        Example:
            >>> df = client.quant.ohlcv_batch(["000001", "600519"])
            >>> print(df[["symbol", "date", "close", "volume"]])
        """
        data: dict[str, Any] = {
            "symbols": symbols,
            "market": market,
        }
        if start_date:
            data["start_date"] = start_date
        if end_date:
            data["end_date"] = end_date

        response = self._client._post("/v1/quant/quotes/ohlcv/batch", json=data)
        return self._to_dataframe(response.get("datas", []))

    # -------------------------------------------------------------------------
    # Backtest
    # -------------------------------------------------------------------------

    def backtest(
        self,
        start_date: str,
        end_date: str,
        symbol: str,
        entry_formula: str,
        *,
        exit_formula: str | None = None,
        market: StockMarket = "cn",
        initial_cash: float = 100000.0,
        commission: float = 0.0,
        stop_loss: float = 0.0,
        sizer_percent: int = 99,
        auto_close: bool = True,
        labels: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Execute strategy backtest

        Args:
            start_date: Backtest start date (YYYY-MM-DD)
            end_date: Backtest end date (YYYY-MM-DD)
            symbol: Stock code
            market: Stock market ("cn", "hk", "us"), default "cn"
            entry_formula: Buy/long entry formula (result > 0 triggers buy)
            exit_formula: Sell/close formula (result > 0 triggers sell), optional
            initial_cash: Initial capital (default: 100000.0)
            commission: Commission rate (default: 0.0)
            stop_loss: Stop loss setting (default: 0.0, no stop loss)
            sizer_percent: Position percentage (default: 99%)
            auto_close: Auto close positions (default: True)
            labels: Label dict for returning extra indicator values, e.g. {"up": "CROSS(MA(20), MA(60))"}

        Returns:
            Backtest results including:
            - success: Whether backtest succeeded
            - initial_cash: Initial capital
            - final_cash: Final capital
            - total_return: Total return
            - total_return_pct: Total return percentage
            - max_drawdown: Maximum drawdown
            - profit_factor: Profit factor
            - win_rate: Win rate
            - total_trades: Total number of trades
            - trades: List of trade details

        Example:
            >>> # Simple golden cross strategy
            >>> result = client.quant.backtest(
            ...     start_date="2023-01-01",
            ...     end_date="2024-01-01",
            ...     symbol="000001",
            ...     entry_formula="CROSS(MA(5), MA(20))",  # Buy when MA5 crosses above MA20
            ...     initial_cash=100000
            ... )
            >>> print(f"Total Return: {result['total_return_pct']:.2%}")
            >>> print(f"Max Drawdown: {result['max_drawdown']:.2%}")
            >>> print(f"Win Rate: {result['win_rate']:.2%}")
            
            >>> # Strategy with entry and exit signals
            >>> result = client.quant.backtest(
            ...     start_date="2023-01-01",
            ...     end_date="2024-01-01",
            ...     symbol="000001",
            ...     entry_formula="CROSS(MA(5), MA(20))",  # Buy signal
            ...     exit_formula="CROSSDOWN(MA(5), MA(20))"  # Sell signal
            ... )
            
            >>> # With custom labels for analysis
            >>> result = client.quant.backtest(
            ...     start_date="2023-01-01",
            ...     end_date="2024-01-01",
            ...     symbol="000001",
            ...     entry_formula="RSI(14) < 30",
            ...     exit_formula="RSI(14) > 70",
            ...     labels={"rsi": "RSI(14)", "ma20": "MA(20)"}
            ... )
        """
        data = {
            "start_date": start_date,
            "end_date": end_date,
            "symbol": symbol,
            "market": market,
            "entry_formula": entry_formula,
            "initial_cash": initial_cash,
            "commission": commission,
            "stop_loss": stop_loss,
            "sizer_percent": sizer_percent,
            "auto_close": auto_close,
        }
        if exit_formula is not None:
            data["exit_formula"] = exit_formula
        if labels is not None:
            data["labels"] = labels

        return self._client._post("/v1/quant/backtest", json=data)

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _to_dataframe(self, data: list[dict[str, Any]]) -> pd.DataFrame:
        """Convert API response to DataFrame"""
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        # Convert date columns if present
        for col in ["date", "check_date", "trade_date"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
        return df
