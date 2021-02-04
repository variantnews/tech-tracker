# tech-tracker
Python3 framework for scraping websites to find pricing and availibility of tech products (gpu, cpu, xbox, ps5)

geckodriver needs to be installed in order to run Selenium (firefox browser automation)
see: https://pypi.org/project/geckodriver-autoinstaller/

Install libraries in requirements.txt

run: pip3 install -r requirements.txt 

Configure .env
- WEBDRIVER_PATH: set path for the geckodriver that was installed
- DISCORD_WEBHOOK_URL: python-dotenv is used to configure Discord webhook notifications.  Obtain webhook url from your Discord Server
- ALERT_DELAY, MIN_DELAY, MAX_DELAY: set alert delay and script exection times.  this executes the sleep command in python and provides a delay as the code iterates through each site
- OPEN_WEB_BROWSER: set to false if code is running on a headless server (no GUI, just shell)

logconfig.py - set local_path with the path to your local logging file. Note ~ is being used to your local user account path is already pre-pended