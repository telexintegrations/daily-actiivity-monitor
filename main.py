from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import httpx
import asyncio
from datetime import datetime
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dau_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('dau_monitor')

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Setting(BaseModel):
    label: str
    type: str
    required: bool
    default: str

class MonitorPayload(BaseModel):
    channel_id: str
    return_url: str
    settings: List[Setting]

    # Add debug helper
    def __str__(self):
        return f"MonitorPayload(channel_id={self.channel_id}, return_url={self.return_url}, settings_count={len(self.settings)})"

async def fetch_dau_data(site: str) -> dict:
    """Fetches the daily active user (DAU) count from portfolio API."""
    logger.debug(f"Attempting to fetch DAU data from site: {site}")
    
    try:
        async with httpx.AsyncClient() as client:
            logger.debug(f"Making GET request to {site}/api/analytics/daily")
            start_time = datetime.now()
            
            response = await client.get(f"{site}/api/analytics/daily", timeout=10)
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.debug(f"Request completed in {duration:.2f} seconds")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully fetched DAU data from {site}: {data}")
                return {"site": site, "dau": data.get("unique_visitors", 0)}
            else:
                error_msg = f"Failed to fetch DAU (status {response.status_code})"
                logger.error(f"{error_msg} from {site}. Response: {response.text}")
                return {"site": site, "error": error_msg}
                
    except httpx.TimeoutException:
        error_msg = "Request timed out"
        logger.error(f"{error_msg} for site: {site}")
        return {"site": site, "error": error_msg}
    except Exception as e:
        logger.exception(f"Unexpected error while fetching DAU from {site}")
        return {"site": site, "error": str(e)}

async def monitor_dau_task(payload: MonitorPayload):
    logger.info(f"Starting monitoring task for payload: {payload}")
    
    # Extract and log sites to monitor
    sites = [s.default for s in payload.settings if s.label.startswith("site")]
    logger.debug(f"Sites to monitor: {sites}")
    
    # Fetch data from all sites
    logger.debug("Initiating parallel DAU data fetch")
    results = await asyncio.gather(*(fetch_dau_data(site) for site in sites))
    logger.debug(f"Fetch results: {json.dumps(results, indent=2)}")
    
    # Format message
    message_lines = [
        f"{result['site']}: {result['dau']} active users"
        if "dau" in result
        else f"{result['site']}: {result['error']}"
        for result in results
    ]
    message = "\n".join(message_lines)
    logger.debug(f"Formatted message: {message}")
    
    # Prepare response data
    data = {
        "message": message,
        "username": "DAU Monitor",
        "event_name": "Daily Active Users Report",
        "status": "success" if all("dau" in r for r in results) else "error"
    }
    logger.debug(f"Prepared response data: {json.dumps(data, indent=2)}")
    
    # Send response
    try:
        logger.debug(f"Sending response to {payload.return_url}")
        async with httpx.AsyncClient() as client:
            response = await client.post(payload.return_url, json=data)
            logger.info(f"Response sent. Status: {response.status_code}")
            if response.status_code != 200:
                logger.error(f"Failed to send response. Status: {response.status_code}, Body: {response.text}")
    except Exception as e:
        logger.exception("Failed to send response")

@app.get("/integration.json")
def get_integration_json(request: Request):
    logger.debug("Fetching integration.json")
    base_url = str(request.base_url).rstrip("/")
    logger.debug(f"Base URL: {base_url}")
    
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
            "integration_category": "Analytics & Monitoring",
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
                {
                    "label": "interval",
                    "type": "text",
                    "required": True,
                    "default": "@hourly"
                }
            ],
            "target_url": "https://portfolio-wahz.onrender.com/api/analytics/daily",
            "tick_url": f"{base_url}/tick"
        }
    }
    logger.debug(f"Returning integration data: {json.dumps(integration_data, indent=2)}")
    return integration_data

@app.post("/tick", status_code=202)
async def monitor(payload: MonitorPayload, background_tasks: BackgroundTasks):
    logger.info(f"Received tick request for channel: {payload.channel_id}")
    logger.debug(f"Full payload: {payload}")
    
    background_tasks.add_task(monitor_dau_task, payload)
    logger.debug("Added monitoring task to background tasks")
    
    return {"status": "accepted"}

# Add error handling middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    
    try:
        response = await call_next(request)
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"{request.method} {request.url.path} completed in {duration:.2f}s - Status: {response.status_code}")
        return response
    except Exception as e:
        logger.exception(f"Request failed: {request.method} {request.url.path}")
        raise