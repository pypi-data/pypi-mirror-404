"""
Market models for Nemati AI SDK.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class StockData:
    """Stock market data."""
    symbol: str
    name: str = ""
    price: float = 0.0
    change: float = 0.0
    change_percent: float = 0.0
    volume: int = 0
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    high_52w: Optional[float] = None
    low_52w: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    previous_close: Optional[float] = None
    updated_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StockData":
        return cls(
            symbol=data.get("symbol", ""),
            name=data.get("name", ""),
            price=data.get("price", 0.0),
            change=data.get("change", 0.0),
            change_percent=data.get("change_percent", data.get("changePercent", 0.0)),
            volume=data.get("volume", 0),
            market_cap=data.get("market_cap", data.get("marketCap")),
            pe_ratio=data.get("pe_ratio", data.get("peRatio")),
            high_52w=data.get("high_52w", data.get("high52w")),
            low_52w=data.get("low_52w", data.get("low52w")),
            open=data.get("open"),
            high=data.get("high"),
            low=data.get("low"),
            previous_close=data.get("previous_close", data.get("previousClose")),
            updated_at=data.get("updated_at"),
        )


@dataclass
class CryptoData:
    """Cryptocurrency data."""
    symbol: str
    name: str = ""
    price: float = 0.0
    change_24h: float = 0.0
    change_percent_24h: float = 0.0
    volume_24h: float = 0.0
    market_cap: Optional[float] = None
    circulating_supply: Optional[float] = None
    total_supply: Optional[float] = None
    max_supply: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    ath: Optional[float] = None
    atl: Optional[float] = None
    updated_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CryptoData":
        return cls(
            symbol=data.get("symbol", ""),
            name=data.get("name", ""),
            price=data.get("price", 0.0),
            change_24h=data.get("change_24h", data.get("change24h", 0.0)),
            change_percent_24h=data.get("change_percent_24h", data.get("changePercent24h", 0.0)),
            volume_24h=data.get("volume_24h", data.get("volume24h", 0.0)),
            market_cap=data.get("market_cap", data.get("marketCap")),
            circulating_supply=data.get("circulating_supply", data.get("circulatingSupply")),
            total_supply=data.get("total_supply", data.get("totalSupply")),
            max_supply=data.get("max_supply", data.get("maxSupply")),
            high_24h=data.get("high_24h", data.get("high24h")),
            low_24h=data.get("low_24h", data.get("low24h")),
            ath=data.get("ath"),
            atl=data.get("atl"),
            updated_at=data.get("updated_at"),
        )


@dataclass
class MarketAnalysis:
    """AI-powered market analysis."""
    symbols: List[str]
    summary: str = ""
    sentiment: str = "neutral"
    news_summary: Optional[str] = None
    technical_summary: Optional[str] = None
    recommendations: List[str] = None
    risk_level: str = "medium"
    credits: float = 0.0
    
    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MarketAnalysis":
        return cls(
            symbols=data.get("symbols", []),
            summary=data.get("summary", ""),
            sentiment=data.get("sentiment", "neutral"),
            news_summary=data.get("news_summary"),
            technical_summary=data.get("technical_summary"),
            recommendations=data.get("recommendations", []),
            risk_level=data.get("risk_level", "medium"),
            credits=data.get("credits", 0.0),
        )
