# Daily Active Users Bot for Telex

## Overview
This project is a **Telex Interval Integration** that sends daily active user reports every 15 minutes to a Telex channel. The bot monitors the portfolio website [salam-portfolio-three.vercel.app](https://salam-portfolio-three.vercel.app/) and reports the number of unique visitors within the last 24 hours.

## Features
- Tracks unique visitors to the portfolio website.
- Stores visitor analytics in an SQLite database.
- Sends active user reports to the Telex channel every 15 minutes.
- Uses a FastAPI backend to handle analytics and tracking.
- Frontend JavaScript integration for logging page views.

## Integration Type
**Interval Integration** - The bot fetches the active users count at regular intervals and posts updates to a Telex channel.

## Technology Stack
- **Backend:** FastAPI, SQLite
- **Frontend:** JavaScript (for tracking visits)
- **Deployment:** Render (backend), Vercel (frontend)

## Installation
### Prerequisites
Ensure you have the following installed:
- Python 3.8+
- FastAPI
- SQLite
- Telex Account & Organization

### Setup
#### Clone the Repository
```sh
  git clone https://github.com/your-repo/telex-daily-active-users-bot.git
  cd telex-daily-active-users-bot
```
#### Install Dependencies
```sh
  pip install fastapi uvicorn sqlite3 requests
```
#### Initialize Database
```python
  import sqlite3
  conn = sqlite3.connect('portfolio_analytics.db')
  c = conn.cursor()
  c.execute('''
      CREATE TABLE IF NOT EXISTS visits (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          visitor_hash TEXT,
          visit_date DATE,
          page_path TEXT
      )
  ''')
  conn.commit()
  conn.close()
```
#### Run the Backend Server
```sh
  uvicorn main:app --host 0.0.0.0 --port 8000
```

## Usage
### Frontend Tracking
Add this JavaScript snippet to track visits:
```javascript
export const trackPageView = async () => {
    try {
      await fetch('https://portfolio-wahz.onrender.com/api/track-visit', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });
    } catch (error) {
      console.error('Failed to track visit:', error);
    }
};
```
### Fetching Daily Active Users
- API Endpoint: `GET /api/analytics/daily`
- Example Response:
```json
{
    "date": "2025-02-21",
    "unique_visitors": 2
}
```

## Telex Integration
### Integration JSON
```json
{
    "type": "interval",
    "name": "Daily Active Users Bot",
    "interval": "15m",
    "endpoint": "https://portfolio-wahz.onrender.com/api/analytics/daily",
    "format": "Daily Active Users Report: {{unique_visitors}} users"
}
```
### Example Message Sent to Telex Channel
```
Daily Active Users Report
https://portfolio-wahz.onrender.com: 2 active users
```

## Deployment
1. **Host Backend**: Deploy FastAPI on Render/Heroku.
2. **Host Frontend**: Deploy tracking script on Vercel.
3. **Telex Integration**:
   - Submit JSON config to Telex.
   - Enable the integration in your organization.

## Screenshots
![Example Telex Report](https://example.com/screenshot.png) *(Replace with actual screenshot)*

## Contributing
1. Fork the repository.
2. Create a new branch.
3. Make your changes and commit using [Conventional Commits](https://www.conventionalcommits.org/).
4. Open a Pull Request.

## License
This project is licensed under the MIT License.

## Contact
- **Developer:** Ayeleru Abdulsalam Oluwaseun
- **Portfolio:** [salam-portfolio-three.vercel.app](https://salam-portfolio-three.vercel.app/)

