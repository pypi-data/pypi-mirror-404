"""
Stock Module

Provides access to stock market data including prices, financial statements,
and company information. Time series data is returned as pandas DataFrame.
"""

from typing import TYPE_CHECKING, Any, Literal

import pandas as pd

if TYPE_CHECKING:
    from reportify_sdk.client import Reportify


class StockModule:
    """
    Stock data module for financial data and market information

    Access through the main client:
        >>> client = Reportify(api_key="xxx")
        >>> income = client.stock.income_statement("US:AAPL")
    """

    def __init__(self, client: "Reportify"):
        self._client = client

    def _post(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._client._post(path, json=json)

    # -------------------------------------------------------------------------
    # Company Information
    # -------------------------------------------------------------------------

    def overview(
        self, symbols: str | None = None, names: str | None = None
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """
        Get company overview including business description, sector, and key metrics

        Args:
            symbols: Stock symbols. You can enter multiple items, separated by commas(,)
                    Example: "US:AAPL,US:MSFT"
            names: Stock names. You can enter multiple items, separated by commas(,)
                  Example: "Apple Inc.,Microsoft"

        Returns:
            Dictionary or list of dictionaries with company overview data

        Example:
            >>> # Single stock by symbol
            >>> info = client.stock.overview(symbols="US:AAPL")
            >>> print(info["name"], info["sector"])
            
            >>> # Multiple stocks by symbols
            >>> infos = client.stock.overview(symbols="US:AAPL,US:MSFT")
            >>> for info in infos:
            ...     print(info["name"])
            
            >>> # Search by name
            >>> info = client.stock.overview(names="Apple Inc.")
        """
        if not symbols and not names:
            raise ValueError("Either symbols or names must be provided")

        data = {}
        if symbols:
            data["symbols"] = symbols
        if names:
            data["names"] = names

        response = self._post("/v1/stock/company-overview", json=data)
        return response

    def shareholders(
        self,
        symbol: str,
        *,
        type: Literal["shareholders", "outstanding_shareholders"] = "shareholders",
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Get list of major shareholders

        Args:
            symbol: Stock symbol
            type: Type of shareholders to return
                - "shareholders": All shareholders
                - "outstanding_shareholders": Outstanding shareholders only
            limit: Number of shareholders to return (default: 10)

        Returns:
            List of shareholders with ownership details
        """
        response = self._post(
            "/v1/stock/company-shareholders",
            json={"symbol": symbol, "type": type, "limit": limit},
        )
        return response if isinstance(response, list) else response.get("shareholders", [])

    # -------------------------------------------------------------------------
    # Financial Statements (returns DataFrame)
    # -------------------------------------------------------------------------

    def income_statement(
        self,
        symbol: str,
        *,
        period: Literal["annual", "quarterly", "cumulative quarterly"] = "annual",
        limit: int = 8,
        start_date: str | None = None,
        end_date: str | None = None,
        calendar: Literal["calendar", "fiscal"] = "fiscal",
        fiscal_year: str | None = None,
        fiscal_quarter: str | None = None,
    ) -> pd.DataFrame:
        """
        Get income statement data

        Args:
            symbol: Stock symbol
            period: Report cycle ("annual", "quarterly", "cumulative quarterly")
            limit: Return latest N records (default: 8)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            calendar: "calendar" or "fiscal" (default: "fiscal")
            fiscal_year: Specific fiscal year (e.g., "2023")
            fiscal_quarter: Specific fiscal quarter (Q1, Q2, Q3, Q4, FY, H1, "Q3 (9 months)")

        Returns:
            DataFrame with income statement data, indexed by date

        Example:
            >>> income = client.stock.income_statement("US:AAPL", period="quarterly")
            >>> print(income[["revenue", "net_income"]].head())
        """
        data: dict[str, Any] = {
            "symbol": symbol,
            "period": period,
            "limit": limit,
            "calendar": calendar,
        }
        if start_date:
            data["start_date"] = start_date
        if end_date:
            data["end_date"] = end_date
        if fiscal_year:
            data["fiscal_year"] = fiscal_year
        if fiscal_quarter:
            data["fiscal_quarter"] = fiscal_quarter

        response = self._post("/v1/stock/company-income-statement", json=data)
        return self._to_dataframe(response)

    def balance_sheet(
        self,
        symbol: str,
        *,
        period: Literal["annual", "quarterly"] = "annual",
        limit: int = 8,
        start_date: str | None = None,
        end_date: str | None = None,
        calendar: Literal["calendar", "fiscal"] = "fiscal",
        fiscal_year: str | None = None,
        fiscal_quarter: str | None = None,
    ) -> pd.DataFrame:
        """
        Get balance sheet data

        Args:
            symbol: Stock symbol
            period: Report cycle ("annual", "quarterly")
            limit: Return latest N records (default: 8)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            calendar: "calendar" or "fiscal" (default: "fiscal")
            fiscal_year: Specific fiscal year (e.g., "2023")
            fiscal_quarter: Specific fiscal quarter (Q1, Q2, Q3, Q4, FY)

        Returns:
            DataFrame with balance sheet data, indexed by date

        Example:
            >>> balance = client.stock.balance_sheet("US:AAPL")
            >>> print(balance[["total_assets", "total_liabilities"]].head())
        """
        data: dict[str, Any] = {
            "symbol": symbol,
            "period": period,
            "limit": limit,
            "calendar": calendar,
        }
        if start_date:
            data["start_date"] = start_date
        if end_date:
            data["end_date"] = end_date
        if fiscal_year:
            data["fiscal_year"] = fiscal_year
        if fiscal_quarter:
            data["fiscal_quarter"] = fiscal_quarter

        response = self._post("/v1/stock/company-balance-sheet", json=data)
        return self._to_dataframe(response)

    def cashflow_statement(
        self,
        symbol: str,
        *,
        period: Literal["annual", "quarterly", "cumulative quarterly"] = "annual",
        limit: int = 8,
        start_date: str | None = None,
        end_date: str | None = None,
        calendar: Literal["calendar", "fiscal"] = "fiscal",
        fiscal_year: str | None = None,
        fiscal_quarter: str | None = None,
    ) -> pd.DataFrame:
        """
        Get cash flow statement data

        Args:
            symbol: Stock symbol
            period: Report cycle ("annual", "quarterly", "cumulative quarterly")
            limit: Return latest N records (default: 8)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            calendar: "calendar" or "fiscal" (default: "fiscal")
            fiscal_year: Specific fiscal year (e.g., "2023")
            fiscal_quarter: Specific fiscal quarter (Q1, Q2, Q3, Q4, FY, H1, "Q3 (9 months)")

        Returns:
            DataFrame with cash flow data, indexed by date

        Example:
            >>> cashflow = client.stock.cashflow_statement("US:AAPL")
            >>> print(cashflow[["operating_cashflow", "free_cashflow"]].head())
        """
        data: dict[str, Any] = {
            "symbol": symbol,
            "period": period,
            "limit": limit,
            "calendar": calendar,
        }
        if start_date:
            data["start_date"] = start_date
        if end_date:
            data["end_date"] = end_date
        if fiscal_year:
            data["fiscal_year"] = fiscal_year
        if fiscal_quarter:
            data["fiscal_quarter"] = fiscal_quarter

        response = self._post("/v1/stock/company-cashflow-statement", json=data)
        return self._to_dataframe(response)

    def revenue_breakdown(
        self,
        symbol: str,
        *,
        period: str | None = None,
        limit: int = 6,
        start_date: str | None = None,
        end_date: str | None = None,
        fiscal_year: str | None = None,
    ) -> pd.DataFrame:
        """
        Get revenue breakdown

        Args:
            symbol: Stock symbol
            period: Report cycle (e.g., "FY", "Q2")
            limit: Return latest N records (default: 6)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            fiscal_year: Specific fiscal year (e.g., "2023")

        Returns:
            DataFrame with revenue breakdown data
        """
        data: dict[str, Any] = {"symbol": symbol, "limit": limit}
        if period:
            data["period"] = period
        if start_date:
            data["start_date"] = start_date
        if end_date:
            data["end_date"] = end_date
        if fiscal_year:
            data["fiscal_year"] = fiscal_year

        response = self._post("/v1/stock/company-revenue-breakdown", json=data)
        return self._to_dataframe(response)

    # -------------------------------------------------------------------------
    # Price Data (returns DataFrame)
    # -------------------------------------------------------------------------

    def prices(
        self,
        symbol: str,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """
        Get historical stock prices with market data

        Args:
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with price data (date, close, volume, market_cap, pe, ps)

        Example:
            >>> prices = client.stock.prices("US:AAPL")
            >>> print(prices[["close", "volume"]].tail())
        """
        data: dict[str, Any] = {"symbol": symbol}
        if start_date:
            data["start_date"] = start_date
        if end_date:
            data["end_date"] = end_date

        response = self._post("/v1/stock/company-prices", json=data)
        return self._to_dataframe(response)

    def quote(self, symbol: str) -> pd.DataFrame:
        """
        Get real-time stock quote

        Args:
            symbol: Stock symbol

        Returns:
            DataFrame with real-time quote data

        Example:
            >>> quote = client.stock.quote("US:AAPL")
            >>> print(quote[["symbol", "price", "change_percent"]])
        """
        response = self._post("/v1/stock/quote-realtime", json={"symbol": symbol})
        return self._to_dataframe(response)

    def index_prices(
        self,
        symbol: str,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """
        Get stock index prices (e.g., HSI, SPX, DJI)

        Args:
            symbol: Index symbol (e.g., "HSI", "SPX", "DJI")
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with index price data
        """
        data: dict[str, Any] = {"symbol": symbol}
        if start_date:
            data["start_date"] = start_date
        if end_date:
            data["end_date"] = end_date

        response = self._post("/v1/stock/index-prices", json=data)
        return self._to_dataframe(response)

    # -------------------------------------------------------------------------
    # Screening and Calendar
    # -------------------------------------------------------------------------

    def screener(
        self,
        *,
        market_cap_more_than: float | None = None,
        market_cap_lower_than: float | None = None,
        price_more_than: float | None = None,
        price_lower_than: float | None = None,
        change_percentage_more_than: float | None = None,
        change_percentage_lower_than: float | None = None,
        volume_more_than: int | None = None,
        volume_lower_than: int | None = None,
        country: str | None = None,
        exchange: str | None = None,
        dividend_yield_more_than: float | None = None,
        dividend_yield_lower_than: float | None = None,
        pe_ttm_more_than: float | None = None,
        pe_ttm_lower_than: float | None = None,
        limit: int = 100,
    ) -> pd.DataFrame:
        """
        Screen stocks based on various criteria

        Args:
            market_cap_more_than: Market cap greater than
            market_cap_lower_than: Market cap less than
            price_more_than: Stock price greater than
            price_lower_than: Stock price less than
            change_percentage_more_than: Change percentage greater than (e.g., 0.02 for 2%)
            change_percentage_lower_than: Change percentage less than (e.g., 0.04 for 4%)
            volume_more_than: Trading volume greater than
            volume_lower_than: Trading volume less than
            country: Country code (e.g., "US", "CN", "HK")
            exchange: Exchange code (e.g., "NASDAQ", "NYSE", "HKEX")
            dividend_yield_more_than: Dividend yield greater than
            dividend_yield_lower_than: Dividend yield less than
            pe_ttm_more_than: PE TTM greater than
            pe_ttm_lower_than: PE TTM less than
            limit: Maximum number of results (default: 100)

        Returns:
            DataFrame with screened stocks

        Example:
            >>> # Find US stocks with PE < 15 and market cap > 1B
            >>> stocks = client.stock.screener(
            ...     country="US",
            ...     pe_ttm_lower_than=15,
            ...     market_cap_more_than=1000000000
            ... )
        """
        data: dict[str, Any] = {"limit": limit}
        if market_cap_more_than is not None:
            data["market_cap_more_than"] = market_cap_more_than
        if market_cap_lower_than is not None:
            data["market_cap_lower_than"] = market_cap_lower_than
        if price_more_than is not None:
            data["price_more_than"] = price_more_than
        if price_lower_than is not None:
            data["price_lower_than"] = price_lower_than
        if change_percentage_more_than is not None:
            data["change_percentage_more_than"] = change_percentage_more_than
        if change_percentage_lower_than is not None:
            data["change_percentage_lower_than"] = change_percentage_lower_than
        if volume_more_than is not None:
            data["volume_more_than"] = volume_more_than
        if volume_lower_than is not None:
            data["volume_lower_than"] = volume_lower_than
        if country:
            data["country"] = country
        if exchange:
            data["exchange"] = exchange
        if dividend_yield_more_than is not None:
            data["dividend_yield_more_than"] = dividend_yield_more_than
        if dividend_yield_lower_than is not None:
            data["dividend_yield_lower_than"] = dividend_yield_lower_than
        if pe_ttm_more_than is not None:
            data["pe_ttm_more_than"] = pe_ttm_more_than
        if pe_ttm_lower_than is not None:
            data["pe_ttm_lower_than"] = pe_ttm_lower_than

        response = self._post("/v1/stock/screener", json=data)
        return self._to_dataframe(response)

    def earnings_calendar(
        self,
        *,
        market: Literal["us", "hk", "cn"] = "us",
        start_date: str | None = None,
        end_date: str | None = None,
        symbol: str | None = None,
    ) -> pd.DataFrame:
        """
        Get earnings announcement calendar

        Args:
            market: Stock market ("us", "hk", "cn")
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            symbol: Filter by specific symbol

        Returns:
            DataFrame with earnings calendar data
        """
        data: dict[str, Any] = {"market": market}
        if start_date:
            data["start_date"] = start_date
        if end_date:
            data["end_date"] = end_date
        if symbol:
            data["symbol"] = symbol

        response = self._post("/v1/stock/earnings-calendar", json=data)
        return self._to_dataframe(response)

    def ipo_calendar_hk(
        self,
        status: Literal["Filing", "Hearing", "Priced"] = "Filing",
    ) -> pd.DataFrame:
        """
        Get Hong Kong IPO calendar

        Args:
            status: IPO status filter ("Filing", "Hearing", "Priced")

        Returns:
            DataFrame with IPO calendar data
        """
        response = self._post("/v1/stock/ipo-calendar-hk", json={"status": status})
        return self._to_dataframe(response)

    def industry_constituents(
        self,
        market: Literal["cn", "hk", "us"],
        name: str,
        *,
        type: str | None = None,
    ) -> pd.DataFrame:
        """
        Get constituent stocks of an industry

        Args:
            market: Stock market ("cn", "hk", "us")
            name: Industry name (e.g., "军工", "Technology")
            type: Industry classification type (optional)
                - cn: "sw" (申万2021, default), "wind", "hs"
                - hk: "hs" (恒生, default)
                - us: "GICS" (default)

        Returns:
            DataFrame with industry constituent stocks

        Example:
            >>> # Get CN defense industry stocks
            >>> stocks = client.stock.industry_constituents("cn", "军工")
            >>> print(stocks[["symbol", "name", "industry_one_level_name"]])
            
            >>> # Get US technology stocks using GICS
            >>> stocks = client.stock.industry_constituents("us", "Technology")
        """
        data = {"market": market, "name": name}
        if type:
            data["type"] = type

        response = self._post("/v1/stock/industry-constituents", json=data)
        return self._to_dataframe(response)

    def index_constituents(self, symbol: str) -> pd.DataFrame:
        """
        Get constituent stocks of an index

        Args:
            symbol: Index symbol (e.g., "000300" for CSI 300, "399006" for ChiNext)

        Returns:
            DataFrame with index constituent stocks

        Example:
            >>> # Get CSI 300 constituent stocks
            >>> stocks = client.stock.index_constituents("000300")
            >>> print(stocks[["market", "symbol"]])
            
            >>> # Get ChiNext constituent stocks
            >>> stocks = client.stock.index_constituents("399006")
        """
        response = self._post("/v1/stock/index-constituents", json={"symbol": symbol})
        return self._to_dataframe(response)

    def index_tracking_funds(self, symbol: str) -> pd.DataFrame:
        """
        Get tracking funds of an index

        Args:
            symbol: Index symbol (e.g., "000300" for CSI 300)

        Returns:
            DataFrame with index tracking funds

        Example:
            >>> # Get CSI 300 tracking funds
            >>> funds = client.stock.index_tracking_funds("000300")
            >>> print(funds[["short_name", "name", "symbol"]])
            
            >>> # Get SSE 50 tracking funds
            >>> funds = client.stock.index_tracking_funds("000016")
        """
        response = self._post("/v1/stock/index-tracking-funds", json={"symbol": symbol})
        return self._to_dataframe(response)

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _to_dataframe(self, data: Any) -> pd.DataFrame:
        """Convert API response to DataFrame"""
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            # Handle nested data structures
            if "data" in data:
                df = pd.DataFrame(data["data"])
            elif "items" in data:
                df = pd.DataFrame(data["items"])
            elif "records" in data:
                df = pd.DataFrame(data["records"])
            else:
                # Try to create DataFrame from dict values
                df = pd.DataFrame([data])
        else:
            df = pd.DataFrame()

        # Set date column as index if present
        date_columns = ["date", "period", "fiscal_date", "report_date"]
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
                df = df.set_index(col)
                break

        return df
