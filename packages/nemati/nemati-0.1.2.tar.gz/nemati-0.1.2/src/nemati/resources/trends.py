"""
Trend Discovery resource for Nemati AI SDK.
"""

from typing import List, Optional

from ..models.trends import TrendSearchResult, TrendItem, TrendAnalysis


class Trends:
    """
    Trend Discovery resource.
    
    Discover and analyze trends across multiple platforms including
    YouTube, TikTok, Reddit, Instagram, and more.
    
    Usage:
        trends = client.trends.search(
            query="artificial intelligence",
            platforms=["youtube", "tiktok"]
        )
        for trend in trends.items:
            print(f"{trend.platform}: {trend.title}")
    """
    
    def __init__(self, http_client):
        self._http = http_client
        
        # Platform-specific clients
        self.youtube = YouTubeTrends(http_client)
        self.tiktok = TikTokTrends(http_client)
        self.reddit = RedditTrends(http_client)
        self.instagram = InstagramTrends(http_client)
        self.google = GoogleTrends(http_client)
    
    def search(
        self,
        query: str,
        platforms: Optional[List[str]] = None,
        timeframe: str = "7d",
        limit: int = 20,
        **kwargs,
    ) -> TrendSearchResult:
        """
        Search for trends across multiple platforms.
        
        Args:
            query: Search query or topic.
            platforms: List of platforms to search. Options:
                      ['youtube', 'tiktok', 'reddit', 'instagram', 'google', 'twitter']
                      If None, searches all available platforms.
            timeframe: Time range for trends. Options:
                      '24h', '7d', '30d', '90d', '1y'
            limit: Maximum results per platform.
            **kwargs: Additional parameters.
        
        Returns:
            TrendSearchResult with trends from all platforms.
        
        Example:
            trends = client.trends.search(
                query="AI tools",
                platforms=["youtube", "reddit"],
                timeframe="7d"
            )
            
            for trend in trends.items:
                print(f"{trend.platform}: {trend.title}")
                print(f"  Engagement: {trend.engagement}")
                print(f"  Growth: {trend.growth_rate}%")
        """
        payload = {
            "query": query,
            "timeframe": timeframe,
            "limit": limit,
            **kwargs,
        }
        
        if platforms:
            payload["platforms"] = platforms
        
        response = self._http.request("POST", "/trends/search/", json=payload)
        return TrendSearchResult.from_dict(response.get("data", response))
    
    def analyze(
        self,
        trend_id: Optional[str] = None,
        url: Optional[str] = None,
        include_sentiment: bool = True,
        include_demographics: bool = False,
        include_related: bool = True,
        **kwargs,
    ) -> TrendAnalysis:
        """
        Analyze a specific trend in detail.
        
        Args:
            trend_id: ID of a trend from search results.
            url: Direct URL to content to analyze.
            include_sentiment: Include sentiment analysis.
            include_demographics: Include demographic insights.
            include_related: Include related trends.
            **kwargs: Additional parameters.
        
        Returns:
            TrendAnalysis with detailed insights.
        """
        payload = {
            "include_sentiment": include_sentiment,
            "include_demographics": include_demographics,
            "include_related": include_related,
            **kwargs,
        }
        
        if trend_id:
            payload["trend_id"] = trend_id
        if url:
            payload["url"] = url
        
        response = self._http.request("POST", "/trends/analyze/", json=payload)
        return TrendAnalysis.from_dict(response.get("data", response))
    
    def platforms(self) -> List[dict]:
        """
        Get list of available platforms and their capabilities.
        
        Returns:
            List of platform info dictionaries.
        """
        response = self._http.request("GET", "/trends/platforms/")
        return response.get("data", response.get("platforms", []))


class PlatformTrends:
    """Base class for platform-specific trend searches."""
    
    platform_name = "base"
    
    def __init__(self, http_client):
        self._http = http_client
    
    def search(
        self,
        query: str,
        timeframe: str = "7d",
        limit: int = 20,
        sort_by: str = "relevance",
        **kwargs,
    ) -> List[TrendItem]:
        """
        Search trends on this specific platform.
        
        Args:
            query: Search query.
            timeframe: Time range ('24h', '7d', '30d', '90d').
            limit: Maximum results.
            sort_by: Sort order ('relevance', 'date', 'engagement', 'growth').
            **kwargs: Platform-specific parameters.
        
        Returns:
            List of TrendItem objects.
        """
        payload = {
            "query": query,
            "platform": self.platform_name,
            "timeframe": timeframe,
            "limit": limit,
            "sort_by": sort_by,
            **kwargs,
        }
        
        response = self._http.request("POST", "/trends/search/", json=payload)
        data = response.get("data", response)
        items = data.get("items", []) if isinstance(data, dict) else data
        return [TrendItem.from_dict(item) for item in items]
    
    def trending(self, limit: int = 20, **kwargs) -> List[TrendItem]:
        """
        Get currently trending content on this platform.
        
        Args:
            limit: Maximum results.
            **kwargs: Platform-specific parameters.
        
        Returns:
            List of TrendItem objects.
        """
        response = self._http.request(
            "GET",
            f"/trends/{self.platform_name}/trending",
            params={"limit": limit, **kwargs},
        )
        data = response.get("data", response)
        items = data.get("items", []) if isinstance(data, dict) else data
        return [TrendItem.from_dict(item) for item in items]


class YouTubeTrends(PlatformTrends):
    """YouTube-specific trend searches."""
    platform_name = "youtube"
    
    def search(
        self,
        query: str,
        timeframe: str = "7d",
        limit: int = 20,
        sort_by: str = "relevance",
        video_type: Optional[str] = None,
        duration: Optional[str] = None,
        **kwargs,
    ) -> List[TrendItem]:
        """
        Search YouTube trends.
        
        Additional Args:
            video_type: Filter by type ('video', 'channel', 'playlist').
            duration: Filter by duration ('short', 'medium', 'long').
        """
        if video_type:
            kwargs["video_type"] = video_type
        if duration:
            kwargs["duration"] = duration
        
        return super().search(query, timeframe, limit, sort_by, **kwargs)


class TikTokTrends(PlatformTrends):
    """TikTok-specific trend searches."""
    platform_name = "tiktok"
    
    def search(
        self,
        query: str,
        timeframe: str = "7d",
        limit: int = 20,
        sort_by: str = "relevance",
        include_sounds: bool = False,
        **kwargs,
    ) -> List[TrendItem]:
        """
        Search TikTok trends.
        
        Additional Args:
            include_sounds: Include trending sounds/audio.
        """
        kwargs["include_sounds"] = include_sounds
        return super().search(query, timeframe, limit, sort_by, **kwargs)


class RedditTrends(PlatformTrends):
    """Reddit-specific trend searches."""
    platform_name = "reddit"
    
    def search(
        self,
        query: str,
        timeframe: str = "7d",
        limit: int = 20,
        sort_by: str = "relevance",
        subreddit: Optional[str] = None,
        **kwargs,
    ) -> List[TrendItem]:
        """
        Search Reddit trends.
        
        Additional Args:
            subreddit: Limit search to specific subreddit.
        """
        if subreddit:
            kwargs["subreddit"] = subreddit
        
        return super().search(query, timeframe, limit, sort_by, **kwargs)


class InstagramTrends(PlatformTrends):
    """Instagram-specific trend searches."""
    platform_name = "instagram"


class GoogleTrends(PlatformTrends):
    """Google Trends searches."""
    platform_name = "google"
    
    def search(
        self,
        query: str,
        timeframe: str = "7d",
        limit: int = 20,
        sort_by: str = "relevance",
        geo: Optional[str] = None,
        **kwargs,
    ) -> List[TrendItem]:
        """
        Search Google Trends.
        
        Additional Args:
            geo: Geographic region code (e.g., 'US', 'GB').
        """
        if geo:
            kwargs["geo"] = geo
        
        return super().search(query, timeframe, limit, sort_by, **kwargs)
