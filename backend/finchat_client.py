"""
FinChat API Client Module
Handles calling FinChat COT prompts and retrieving results
"""
import os
import asyncio
import aiohttp
import logging
from typing import Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class FinChatClient:
    """Client for interacting with FinChat API"""
    
    def __init__(self, api_url: Optional[str] = None, api_token: Optional[str] = None):
        """
        Initialize FinChat client
        
        Args:
            api_url: FinChat API base URL (defaults to FINCHAT_API_URL env var or https://finchat-api.adgo.io)
            api_token: Optional bearer token for authentication (defaults to FINCHAT_API_TOKEN env var, but not required)
        """
        self.api_url = api_url or os.getenv("FINCHAT_API_URL") or "https://finchat-api.adgo.io"
        self.api_token = api_token or os.getenv("FINCHAT_API_TOKEN")
        
        # Remove trailing slash
        self.api_url = self.api_url.rstrip('/')
        
        # API token is optional - FinChat API doesn't require authentication
        if self.api_token:
            logger.info(f"FinChat client initialized with API URL: {self.api_url} (with authentication)")
        else:
            logger.info(f"FinChat client initialized with API URL: {self.api_url} (no authentication)")
    
    async def create_session(self, client_id: Optional[str] = None, data_source: str = "alpha_vantage") -> str:
        """
        Create a new FinChat session
        
        Args:
            client_id: Optional unique client identifier
            data_source: Data source ("alpha_vantage" or "edgar")
        
        Returns:
            Session ID
        """
        url = f"{self.api_url}/api/v1/sessions/"
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        payload = {
            "data_source": data_source
        }
        if client_id:
            payload["client_id"] = client_id
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
                session_id = data.get("id")
                logger.debug(f"Created FinChat session: {session_id}")
                return session_id
    
    async def run_cot(
        self,
        cot_slug: str,
        ticker: str,
        session_id: Optional[str] = None,
        additional_params: Optional[Dict[str, str]] = None,
        max_poll_attempts: int = 60,
        poll_interval_seconds: int = 5
    ) -> Dict[str, Any]:
        """
        Run a FinChat COT prompt and wait for completion
        
        Args:
            cot_slug: The COT slug identifier
            ticker: Ticker symbol to analyze
            session_id: Optional session ID (creates new if not provided)
            additional_params: Additional parameters to pass to COT (e.g., {"date": "2024-01-01"})
            max_poll_attempts: Maximum number of polling attempts
            poll_interval_seconds: Seconds between polling attempts
        
        Returns:
            Dictionary with result_id, content, and metadata
        """
        # Create session if not provided
        if not session_id:
            session_id = await self.create_session(client_id=f"backtester-{datetime.now().timestamp()}")
        
        # Construct COT message
        # Use stock_symbol if provided in additional_params, otherwise use ticker
        stock_symbol = additional_params.get("stock_symbol", ticker) if additional_params else ticker
        cot_message = f"cot {cot_slug} $stock_symbol:{stock_symbol}"
        
        if additional_params:
            for key, value in additional_params.items():
                # Skip stock_symbol as we already added it, and ticker if stock_symbol was provided
                if key == "stock_symbol" or (key == "ticker" and "stock_symbol" in additional_params):
                    continue
                cot_message += f" ${key}:{value}"
        
        # Send COT chat message
        cot_chat_id = await self._send_cot_message(session_id, cot_message)
        logger.info(f"Started COT {cot_slug} for {ticker}, chat ID: {cot_chat_id}")
        
        # Poll for completion
        completion = await self._poll_for_completion(
            session_id,
            cot_chat_id,
            max_attempts=max_poll_attempts,
            interval_seconds=poll_interval_seconds
        )
        
        # Get result content
        result_content = await self._get_result(completion["result_id"])
        
        return {
            "session_id": session_id,
            "chat_id": cot_chat_id,
            "result_id": completion["result_id"],
            "content": result_content.get("content", ""),
            "content_translated": result_content.get("content_translated", ""),
            "metadata": completion.get("metadata", {})
        }
    
    async def _send_cot_message(self, session_id: str, message: str) -> str:
        """Send a COT chat message"""
        url = f"{self.api_url}/api/v1/chats/"
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        payload = {
            "session": session_id,
            "message": message
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("id")
    
    async def _poll_for_completion(
        self,
        session_id: str,
        cot_chat_id: str,
        max_attempts: int = 60,
        interval_seconds: int = 5
    ) -> Dict[str, Any]:
        """Poll for COT completion"""
        url = f"{self.api_url}/api/v1/chats/"
        headers = {}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        params = {
            "session_id": session_id,
            "page_size": 500
        }
        
        for attempt in range(max_attempts):
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    response.raise_for_status()
                    data = await response.json()
                    chats = data.get("results", [])
                    
                    # Find the response chat
                    response_chat = next(
                        (chat for chat in chats if chat.get("respond_to") == cot_chat_id),
                        None
                    )
                    
                    if not response_chat:
                        # No response yet, wait and retry
                        await asyncio.sleep(interval_seconds)
                        continue
                    
                    # Check for errors
                    if response_chat.get("intent") == "error":
                        error_msg = response_chat.get("message", "COT execution failed")
                        raise RuntimeError(f"FinChat COT execution failed: {error_msg}")
                    
                    # Check if complete (has result_id)
                    if response_chat.get("result_id"):
                        logger.info(f"COT completed after {attempt + 1} polling attempts")
                        return {
                            "response_chat_id": response_chat.get("id"),
                            "result_id": response_chat.get("result_id"),
                            "metadata": response_chat.get("metadata", {})
                        }
                    
                    # Still running - log progress
                    metadata = response_chat.get("metadata", {})
                    if metadata:
                        progress = metadata.get("current_progress", 0)
                        total = metadata.get("total_progress", 100)
                        step = metadata.get("current_step", "Processing...")
                        if total > 0:
                            pct = (progress / total) * 100
                            logger.debug(f"COT progress: {pct:.1f}% - {step}")
                    
                    # Wait before next poll
                    await asyncio.sleep(interval_seconds)
        
        raise TimeoutError(f"FinChat COT execution timed out after {max_attempts} attempts")
    
    async def _get_result(self, result_id: str) -> Dict[str, Any]:
        """Get result content by result ID"""
        url = f"{self.api_url}/api/v1/results/{result_id}/"
        headers = {}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                return await response.json()
    
    def parse_cot_result(self, content: str) -> Dict[str, Any]:
        """
        Parse COT result content to extract buy/sell/hold signal
        
        This is a basic parser. You may need to customize based on your COT output format.
        All signal detection is case-insensitive.
        
        Args:
            content: The COT result content (markdown text)
        
        Returns:
            Dictionary with signal, confidence, and reasoning
        """
        # Convert to lowercase for case-insensitive matching
        content_lower = content.lower()
        
        # Look for explicit signals
        signal = None
        confidence = 0.5  # Default confidence
        
        # Check for buy signals
        if any(keyword in content_lower for keyword in ["buy", "purchase", "long", "enter", "should buy"]):
            signal = "buy"
            # Try to extract confidence if mentioned
            if "strong buy" in content_lower or "highly recommend" in content_lower:
                confidence = 0.9
            elif "moderate buy" in content_lower or "recommend buy" in content_lower:
                confidence = 0.7
            else:
                confidence = 0.6
        
        # Check for sell signals
        elif any(keyword in content_lower for keyword in ["sell", "exit", "close", "short", "should sell"]):
            signal = "sell"
            if "strong sell" in content_lower or "highly recommend sell" in content_lower:
                confidence = 0.9
            elif "moderate sell" in content_lower or "recommend sell" in content_lower:
                confidence = 0.7
            else:
                confidence = 0.6
        
        # Check for hold signals
        elif any(keyword in content_lower for keyword in ["hold", "maintain", "keep", "retain", "should hold"]):
            signal = "hold"
            confidence = 0.5
        
        # If no explicit signal found, try to infer from sentiment
        if signal is None:
            positive_words = ["positive", "bullish", "upward", "growth", "increase", "good", "strong"]
            negative_words = ["negative", "bearish", "downward", "decline", "decrease", "weak", "poor"]
            
            positive_count = sum(1 for word in positive_words if word in content_lower)
            negative_count = sum(1 for word in negative_words if word in content_lower)
            
            if positive_count > negative_count:
                signal = "buy"
                confidence = 0.6
            elif negative_count > positive_count:
                signal = "sell"
                confidence = 0.6
            else:
                signal = "hold"
                confidence = 0.5
        
        return {
            "signal": signal,
            "confidence": confidence,
            "reasoning": content[:500]  # First 500 chars as reasoning
        }

