curl --location 'https://project-it.onrender.com/tick' \
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
				"label": "interval",
				"type": "text",
				"required": true,
				"default": "* * * * *"
			}
    ]
}'