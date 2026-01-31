"""
Trends models for Nemati AI SDK.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class TrendItem:
    """A single trend item."""
    id: str
    platform: str
    title: str
    url: Optional[str] = None
    thumbnail: Optional[str] = None
    author: Optional[str] = None
    engagement: int = 0
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    growth_rate: float = 0.0
    published_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrendItem":
        return cls(
            id=data.get("id", ""),
            platform=data.get("platform", ""),
            title=data.get("title", ""),
            url=data.get("url"),
            thumbnail=data.get("thumbnail"),
            author=data.get("author"),
            engagement=data.get("engagement", 0),
            views=data.get("views", 0),
            likes=data.get("likes", 0),
            comments=data.get("comments", 0),
            shares=data.get("shares", 0),
            growth_rate=data.get("growth_rate", 0.0),
            published_at=data.get("published_at"),
        )


@dataclass
class TrendSearchResult:
    """Results from trend search."""
    items: List[TrendItem]
    query: str = ""
    total_results: int = 0
    platforms: List[str] = None
    credits: float = 0.0
    
    def __post_init__(self):
        if self.platforms is None:
            self.platforms = []
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrendSearchResult":
        items_data = data.get("items", data.get("trends", []))
        items = [TrendItem.from_dict(item) for item in items_data]
        
        return cls(
            items=items,
            query=data.get("query", ""),
            total_results=data.get("total_results", len(items)),
            platforms=data.get("platforms", []),
            credits=data.get("credits", 0.0),
        )
    
    def __iter__(self):
        return iter(self.items)
    
    def __len__(self):
        return len(self.items)


@dataclass
class SentimentAnalysis:
    """Sentiment analysis results."""
    positive: float = 0.0
    negative: float = 0.0
    neutral: float = 0.0
    overall: str = "neutral"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SentimentAnalysis":
        return cls(
            positive=data.get("positive", 0.0),
            negative=data.get("negative", 0.0),
            neutral=data.get("neutral", 0.0),
            overall=data.get("overall", "neutral"),
        )


@dataclass
class TrendAnalysis:
    """Detailed trend analysis."""
    trend_id: str
    title: str
    summary: str = ""
    sentiment: Optional[SentimentAnalysis] = None
    keywords: List[str] = None
    related_trends: List[TrendItem] = None
    demographics: Optional[Dict[str, Any]] = None
    recommendations: List[str] = None
    credits: float = 0.0
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.related_trends is None:
            self.related_trends = []
        if self.recommendations is None:
            self.recommendations = []
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrendAnalysis":
        sentiment_data = data.get("sentiment")
        sentiment = SentimentAnalysis.from_dict(sentiment_data) if sentiment_data else None
        
        related_data = data.get("related_trends", [])
        related_trends = [TrendItem.from_dict(t) for t in related_data]
        
        return cls(
            trend_id=data.get("trend_id", ""),
            title=data.get("title", ""),
            summary=data.get("summary", ""),
            sentiment=sentiment,
            keywords=data.get("keywords", []),
            related_trends=related_trends,
            demographics=data.get("demographics"),
            recommendations=data.get("recommendations", []),
            credits=data.get("credits", 0.0),
        )
