"""Monitoring and alerting system with webhook support."""
import httpx
import json
from typing import Dict, Any, Optional
from datetime import datetime
from ..config import settings


async def maybe_alert(
    metric: str,
    value: float,
    threshold: float,
    context: Dict[str, Any]
) -> bool:
    """Send webhook alert if threshold is breached."""
    
    if not settings.alert_webhook_url:
        return False
    
    # Check if threshold is breached
    if value <= threshold:
        return False
    
    # Prepare alert payload
    payload = {
        "timestamp": datetime.utcnow().isoformat(),
        "metric": metric,
        "value": value,
        "threshold": threshold,
        "breach_amount": value - threshold,
        "context": context
    }
    
    try:
        # Send webhook
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.alert_webhook_url,
                json=payload,
                timeout=10.0
            )
            
            if response.status_code == 200:
                print(f"Alert sent for {metric}: {value} > {threshold}")
                return True
            else:
                print(f"Alert webhook failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"Error sending alert: {e}")
        return False


class AlertThresholds:
    """Default alert thresholds."""
    LATENCY_MS = 1000  # 1 second
    ERROR_RATE = 0.05  # 5% error rate
    PASS_COST_USD = 10.0  # $10 per pass
    TOKEN_USAGE = 10000  # 10k tokens per request