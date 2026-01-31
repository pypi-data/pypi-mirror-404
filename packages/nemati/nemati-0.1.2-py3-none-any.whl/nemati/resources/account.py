"""
Account resource for Nemati AI SDK.
"""

from typing import Optional

from ..models.account import AccountInfo, Credits, Usage, Limits


class Account:
    """
    Account resource for managing your Nemati AI account.
    
    Check credits, usage, limits, and account information.
    
    Usage:
        # Check credits
        credits = client.account.credits()
        print(f"Remaining: {credits.remaining}")
        
        # Get usage
        usage = client.account.usage()
        print(f"Total requests: {usage.total_requests}")
    """
    
    def __init__(self, http_client):
        self._http = http_client
    
    def me(self) -> AccountInfo:
        """
        Get current account information.
        
        Returns:
            AccountInfo with email, plan, and account details.
        
        Example:
            account = client.account.me()
            print(f"Email: {account.email}")
            print(f"Plan: {account.plan.name}")
        """
        response = self._http.request("GET", "/account/me/")
        return AccountInfo.from_dict(response.get("data", response))
    
    def credits(self) -> Credits:
        """
        Get current credit balance.
        
        Returns:
            Credits with balance information.
        
        Example:
            credits = client.account.credits()
            print(f"Total: {credits.total}")
            print(f"Used: {credits.used}")
            print(f"Remaining: {credits.remaining}")
        """
        response = self._http.request("GET", "/account/credits/")
        return Credits.from_dict(response.get("data", response))
    
    def usage(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        group_by: str = "day",
    ) -> Usage:
        """
        Get usage statistics.
        
        Args:
            start_date: Start date (YYYY-MM-DD format).
            end_date: End date (YYYY-MM-DD format).
            group_by: Grouping period ('hour', 'day', 'week', 'month').
        
        Returns:
            Usage with detailed statistics.
        
        Example:
            usage = client.account.usage(
                start_date="2026-01-01",
                end_date="2026-01-31"
            )
            print(f"Chat requests: {usage.chat.requests}")
            print(f"Images generated: {usage.image.count}")
        """
        params = {"group_by": group_by}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        response = self._http.request("GET", "/account/usage/", params=params)
        return Usage.from_dict(response.get("data", response))
    
    def limits(self) -> Limits:
        """
        Get current plan limits.
        
        Returns:
            Limits for all features based on your plan.
        
        Example:
            limits = client.account.limits()
            print(f"Chat messages/day: {limits.chat.max_messages_per_day}")
            print(f"Image generations/day: {limits.image.max_per_day}")
        """
        response = self._http.request("GET", "/account/limits/")
        return Limits.from_dict(response.get("data", response))
    
    def api_keys(self) -> list:
        """
        List API keys for this account.
        
        Returns:
            List of API key info (without the actual key values).
        """
        response = self._http.request("GET", "/account/api-keys/")
        return response.get("data", response.get("api_keys", []))
