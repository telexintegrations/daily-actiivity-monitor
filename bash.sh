curl --location 'http://127.0.0.1:8000/tick' \
--header 'Content-Type: application/json' \
--data '{
    "channel_id": "0195204d-4679-75ff-8d14-3fbed758cb3d",
    "return_url": "https://ping.telex.im/v1/return/0195204d-4679-75ff-8d14-3fbed758cb3d",
    "settings": [
            {
       
				"label": "site-1", 
				"default": "https://portfolio-wahz.onrender.com",
				"type": "text",
				"required": true
			},
			{
       
				"label": "frontend-site",
				"default": "https://salam-portfolio-three.vercel.app/",
				"type": "text",
				"required": true
			},
			{
				"label": "interval",
				"type": "text",
				"required": true,
				"default": "* * * * *"
			}
    ]
}'