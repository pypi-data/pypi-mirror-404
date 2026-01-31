"""
Market Intelligence resource for Nemati AI SDK.
"""

from typing import List, Optional

from ..models.market import StockData, CryptoData, MarketAnalysis


class Market:
    """
    Market Intelligence resource.
    
    Access stock and cryptocurrency data with AI-powered analysis.
    
    Usage:
        # Stock data
        stock = client.market.stocks.get("AAPL")
        print(f"Price: ${stock.price}")
        
        # Crypto data
        crypto = client.market.crypto.get("BTC")
        print(f"Price: ${crypto.price}")
    """
    
    def __init__(self, http_client):
        self._http = http_client
        self.stocks = Stocks(http_client)
        self.crypto = Crypto(http_client)
    
    def analyze(
        self,
        symbols: List[str],
        include_news: bool = True,
        include_sentiment: bool = True,
        include_technicals: bool = False,
        **kwargs,
    ) -> MarketAnalysis:
        """
        Get AI-powered market analysis for multiple symbols.
        
        Args:
            symbols: List of stock/crypto symbols to analyze.
            include_news: Include recent news analysis.
            include_sentiment: Include market sentiment.
            include_technicals: Include technical analysis indicators.
            **kwargs: Additional parameters.
        
        Returns:
            MarketAnalysis with AI insights.
        
        Example:
            analysis = client.market.analyze(
                symbols=["AAPL", "GOOGL", "MSFT"],
                include_news=True
            )
            print(analysis.summary)
        """
        payload = {
            "symbols": symbols,
            "include_news": include_news,
            "include_sentiment": include_sentiment,
            "include_technicals": include_technicals,
            **kwargs,
        }
        
        response = self._http.request("POST", "/market/analyze/", json=payload)
        return MarketAnalysis.from_dict(response.get("data", response))
    
    def search(
        self,
        query: str,
        type: Optional[str] = None,
        limit: int = 10,
    ) -> List[dict]:
        """
        Search for stocks and cryptocurrencies.
        
        Args:
            query: Search query (name or symbol).
            type: Filter by type ('stock', 'crypto').
            limit: Maximum results.
        
        Returns:
            List of matching symbols.
        """
        params = {"query": query, "limit": limit}
        if type:
            params["type"] = type
        
        response = self._http.request("GET", "/market/search/", params=params)
        return response.get("data", response.get("results", []))


class Stocks:
    """Stock market data."""
    
    def __init__(self, http_client):
        self._http = http_client
    
    def get(
        self,
        symbol: str,
        **kwargs,
    ) -> StockData:
        """
        Get stock data for a symbol.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'GOOGL').
            **kwargs: Additional parameters.
        
        Returns:
            StockData with current price and info.
        
        Example:
            stock = client.market.stocks.get("AAPL")
            print(f"Price: ${stock.price}")
            print(f"Change: {stock.change_percent}%")
        """
        response = self._http.request("GET", f"/market/stocks/{symbol}", params=kwargs)
        return StockData.from_dict(response.get("data", response))
    
    def history(
        self,
        symbol: str,
        period: str = "1mo",
        interval: str = "1d",
        **kwargs,
    ) -> List[dict]:
        """
        Get historical stock data.
        
        Args:
            symbol: Stock symbol.
            period: Time period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '5y', 'max').
            interval: Data interval ('1m', '5m', '15m', '1h', '1d', '1wk', '1mo').
            **kwargs: Additional parameters.
        
        Returns:
            List of historical data points.
        """
        params = {
            "period": period,
            "interval": interval,
            **kwargs,
        }
        
        response = self._http.request("GET", f"/market/stocks/{symbol}/history", params=params)
        return response.get("data", response.get("history", []))
    
    def quote(self, symbols: List[str]) -> List[StockData]:
        """
        Get quotes for multiple stocks.
        
        Args:
            symbols: List of stock symbols.
        
        Returns:
            List of StockData objects.
        """
        response = self._http.request(
            "GET",
            "/market/stocks/quote",
            params={"symbols": ",".join(symbols)},
        )
        return [
            StockData.from_dict(s)
            for s in response.get("data", response.get("quotes", []))
        ]


class Crypto:
    """Cryptocurrency data."""
    
    def __init__(self, http_client):
        self._http = http_client
    
    def get(
        self,
        symbol: str,
        **kwargs,
    ) -> CryptoData:
        """
        Get cryptocurrency data.
        
        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH').
            **kwargs: Additional parameters.
        
        Returns:
            CryptoData with current price and info.
        
        Example:
            btc = client.market.crypto.get("BTC")
            print(f"Price: ${btc.price}")
            print(f"24h Volume: ${btc.volume_24h}")
        """
        response = self._http.request("GET", f"/market/crypto/{symbol}", params=kwargs)
        return CryptoData.from_dict(response.get("data", response))
    
    def history(
        self,
        symbol: str,
        period: str = "1mo",
        interval: str = "1d",
        **kwargs,
    ) -> List[dict]:
        """
        Get historical crypto data.
        
        Args:
            symbol: Crypto symbol.
            period: Time period.
            interval: Data interval.
            **kwargs: Additional parameters.
        
        Returns:
            List of historical data points.
        """
        params = {
            "period": period,
            "interval": interval,
            **kwargs,
        }
        
        response = self._http.request("GET", f"/market/crypto/{symbol}/history", params=params)
        return response.get("data", response.get("history", []))
    
    def list(
        self,
        limit: int = 100,
        sort_by: str = "market_cap",
    ) -> List[CryptoData]:
        """
        List top cryptocurrencies.
        
        Args:
            limit: Maximum results.
            sort_by: Sort order ('market_cap', 'volume', 'change').
        
        Returns:
            List of CryptoData objects.
        """
        response = self._http.request(
            "GET",
            "/market/crypto",
            params={"limit": limit, "sort_by": sort_by},
        )
        return [
            CryptoData.from_dict(c)
            for c in response.get("data", response.get("coins", []))
        ]
