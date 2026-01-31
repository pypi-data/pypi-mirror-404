"""
Account models for Nemati AI SDK.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Plan:
    """Subscription plan info."""
    id: str
    name: str
    price: float = 0.0
    credits_per_month: int = 0
    is_monthly: bool = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Plan":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", data.get("title", "")),
            price=data.get("price", 0.0),
            credits_per_month=data.get("credits_per_month", data.get("credit", 0)),
            is_monthly=data.get("is_monthly", True),
        )


@dataclass
class AccountInfo:
    """Account information."""
    id: str
    email: str
    name: Optional[str] = None
    plan: Optional[Plan] = None
    created_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AccountInfo":
        plan_data = data.get("plan")
        plan = Plan.from_dict(plan_data) if plan_data else None
        
        return cls(
            id=data.get("id", ""),
            email=data.get("email", ""),
            name=data.get("name"),
            plan=plan,
            created_at=data.get("created_at"),
        )


@dataclass
class Credits:
    """Credit balance information."""
    total: float = 0.0
    used: float = 0.0
    remaining: float = 0.0
    base_credit: float = 0.0
    referral_bonus: float = 0.0
    daily_bonus: float = 0.0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Credits":
        total = data.get("total", data.get("total_credit", 0.0))
        used = data.get("used", 0.0)
        remaining = data.get("remaining", total - used)
        
        return cls(
            total=total,
            used=used,
            remaining=remaining,
            base_credit=data.get("base_credit", data.get("credit", 0.0)),
            referral_bonus=data.get("referral_bonus", 0.0),
            daily_bonus=data.get("daily_bonus", 0.0),
        )


@dataclass
class ServiceUsage:
    """Usage for a specific service."""
    requests: int = 0
    tokens: int = 0
    credits: float = 0.0
    count: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServiceUsage":
        return cls(
            requests=data.get("requests", data.get("count", 0)),
            tokens=data.get("tokens", 0),
            credits=data.get("credits", 0.0),
            count=data.get("count", data.get("requests", 0)),
        )


@dataclass
class Usage:
    """Usage statistics."""
    total_requests: int = 0
    total_tokens: int = 0
    total_credits: float = 0.0
    chat: Optional[ServiceUsage] = None
    writer: Optional[ServiceUsage] = None
    image: Optional[ServiceUsage] = None
    audio: Optional[ServiceUsage] = None
    trends: Optional[ServiceUsage] = None
    market: Optional[ServiceUsage] = None
    documents: Optional[ServiceUsage] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Usage":
        def get_service(key):
            d = data.get(key)
            return ServiceUsage.from_dict(d) if d else None
        
        return cls(
            total_requests=data.get("total_requests", 0),
            total_tokens=data.get("total_tokens", 0),
            total_credits=data.get("total_credits", 0.0),
            chat=get_service("chat"),
            writer=get_service("writer"),
            image=get_service("image"),
            audio=get_service("audio"),
            trends=get_service("trends"),
            market=get_service("market"),
            documents=get_service("documents"),
        )


@dataclass
class ServiceLimits:
    """Limits for a specific service."""
    enabled: bool = True
    max_per_day: int = 0
    max_per_month: int = 0
    rate_limit_per_minute: int = 0
    max_tokens: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServiceLimits":
        return cls(
            enabled=data.get("enabled", True),
            max_per_day=data.get("max_per_day", data.get("max_messages_per_day", 0)),
            max_per_month=data.get("max_per_month", data.get("max_messages_per_month", 0)),
            rate_limit_per_minute=data.get("rate_limit_per_minute", 0),
            max_tokens=data.get("max_tokens", data.get("max_tokens_per_day", 0)),
        )


@dataclass
class Limits:
    """Plan limits for all services."""
    plan_name: str = ""
    chat: Optional[ServiceLimits] = None
    writer: Optional[ServiceLimits] = None
    image: Optional[ServiceLimits] = None
    audio: Optional[ServiceLimits] = None
    trends: Optional[ServiceLimits] = None
    market: Optional[ServiceLimits] = None
    documents: Optional[ServiceLimits] = None
    upload: Optional[ServiceLimits] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Limits":
        def get_service(key):
            d = data.get(key, data.get("limits", {}).get(key))
            return ServiceLimits.from_dict(d) if d else None
        
        return cls(
            plan_name=data.get("plan_name", data.get("plan", {}).get("title", "")),
            chat=get_service("chat"),
            writer=get_service("writer") or get_service("ai_writer"),
            image=get_service("image"),
            audio=get_service("audio"),
            trends=get_service("trends") or get_service("trend_discovery"),
            market=get_service("market") or get_service("market_intel"),
            documents=get_service("documents") or get_service("chat_pdf"),
            upload=get_service("upload"),
        )
