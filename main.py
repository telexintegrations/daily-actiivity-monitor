from fastapi import FastAPI, Request, BackgroundTasks, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, validator
from typing import List, Optional
from datetime import datetime
import httpx
import asyncio
import logging
import json
from functools import lru_cache
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configuration class
class Settings:
    ALLOWED_ORIGINS: List[str] = ["https://your-domain.com"]
    REQUEST_TIMEOUT: int = 10
    MAX_RETRIES: int = 3
    CACHE_TTL: int = 300  # 5 minutes
    LOG_LEVEL: str = "INFO"

@lru_cache()
def get_settings():
    return Settings()

# Enhanced models with validation
class Setting(BaseModel):
    label: str
    type: str
    required: bool
    default: str

    @validator('label')
    def validate_label(cls, v):
        allowed_prefixes = ['site-', 'frontend-', 'interval']
        if not any(v.startswith(prefix) for prefix in allowed_prefixes):
            raise ValueError(f"Label must start with one of: {allowed_prefixes}")
        return v

class MonitorPayload(BaseModel):
    channel_id: str
    return_url: HttpUrl  # Validates URL format
    settings: List[Setting]

    @validator('settings')
    def validate_settings(cls, v):
        site_count = sum(1 for s in v if s.label.startswith('site-'))
        frontend_count = sum(1 for s in v if s.label.startswith('frontend-'))
        if site_count == 0:
            raise ValueError("At least one site must be specified")
        if frontend_count > site_count:
            raise ValueError("Cannot have more frontend sites than monitoring sites")
        return v

class DAUResponse(BaseModel):
    site: str
    dau: Optional[int]
    error: Optional[str]
    timestamp: datetime

# Initialize FastAPI with rate limiting
app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Secure CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=Settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

async def fetch_dau_data(site: str, settings: Settings) -> DAUResponse:
    """Fetches DAU data with retry logic and proper error handling."""
    for attempt in range(settings.MAX_RETRIES):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{site}/api/analytics/daily",
                    timeout=settings.REQUEST_TIMEOUT
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return DAUResponse(
                        site=site,
                        dau=data.get("unique_visitors", 0),
                        error=None,
                        timestamp=datetime.now()
                    )
                
                if response.status_code >= 400:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    if attempt == settings.MAX_RETRIES - 1:
                        return DAUResponse(
                            site=site,
                            dau=None,
                            error=error_msg,
                            timestamp=datetime.now()
                        )
                        
        except Exception as e:
            if attempt == settings.MAX_RETRIES - 1:
                return DAUResponse(
                    site=site,
                    dau=None,
                    error=str(e),
                    timestamp=datetime.now()
                )
        
        await asyncio.sleep(2 ** attempt)  # Exponential backoff

async def monitor_dau_task(payload: MonitorPayload, settings: Settings):
    """Enhanced monitoring task with better error handling and reporting."""
    try:
        sites = [s.default for s in payload.settings if s.label.startswith("site")]
        frontend_sites = {
            s.label.split('-')[1]: s.default 
            for s in payload.settings 
            if s.label.startswith("frontend")
        }

        results = await asyncio.gather(
            *(fetch_dau_data(site, settings) for site in sites)
        )

        # Format message with better error handling
        message_lines = []
        for i, result in enumerate(results):
            site_num = str(i + 1)
            frontend = frontend_sites.get(site_num, "N/A")
            
            if result.dau is not None:
                message_lines.append(
                    f"{result.site}: {result.dau} active users "
                    f"(Frontend: {frontend})"
                )
            else:
                message_lines.append(
                    f"{result.site}: Error - {result.error}"
                )

        status = "success" if all(r.dau is not None for r in results) else "error"
        
        async with httpx.AsyncClient() as client:
            await client.post(
                str(payload.return_url),
                json={
                    "message": "\n".join(message_lines),
                    "username": "DAU Monitor",
                    "event_name": "Daily Active Users Report",
                    "status": status,
                    "timestamp": datetime.now().isoformat()
                }
            )

    except Exception as e:
        logging.exception("Failed to complete monitoring task")
        # Here you might want to implement a dead letter queue
        # or alert system for failed tasks

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/integration.json")
@limiter.limit("60/minute")
def get_integration_json(request: Request):
    base_url = str(request.base_url).rstrip("/")
    
    integration_data = {
        "data": {
            "author": "Blackfox",
            "date": {
                "created_at": "2025-02-13",
                "updated_at": "2025-02-13"
            },
            "descriptions": {
                "app_description": "A bot that monitors the number of daily active users (DAU) on a platform.",
                "app_logo": "https://img.icons8.com/?size=100&id=37410&format=png&color=000000",
                "app_name": "Telex DAU Monitor",
                "app_url": "https://project-it.onrender.com",
                "background_color": "#ffffff"
            },
            "integration_category": "Monitoring & Logging",
            "integration_type": "interval",
            "is_active": True,
            "key_features": [
                "Receive messages from Telex channels.",
                "Fetch daily active users (DAU) from website analytics.",
                "Format messages based on predefined templates or logic.",
                "Send DAU reports back to the Telex channel.",
                "Log DAU tracking activity for auditing purposes."
            ],
            "permissions": {
                "events": [
                    "Receive messages from Telex channels.",
                    "Fetch DAU metrics from website analytics API.",
                    "Format DAU reports.",
                    "Send DAU updates back to the channel.",
                    "Log DAU tracking activity for auditing purposes."
                ]
            },
            "settings": [
                {"label": "site-1", "type": "text", "required": True, "default": ""},
                {"label": "frontend-site","type":"text", "required":False,"default": ""},
                {
                    "label": "interval",
                    "type": "text",
                    "required": True,
                    "default": "@hourly"
                }
            ],
            "target_url": "https://portfolio-wahz.onrender.com",
            "tick_url": f"{base_url}/tick"
        }
    }
    return integration_data

@app.post("/tick", status_code=202)
@limiter.limit("30/minute")
async def monitor(
    request: Request,  # Add this parameter
    payload: MonitorPayload,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings)
):
    background_tasks.add_task(monitor_dau_task, payload, settings)
    return {
        "status": "accepted",
        "timestamp": datetime.now().isoformat()
    }