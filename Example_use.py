from TradeStationClient import CreateTSClient as ct
import pandas as pd
from datetime import datetime, timedelta
import json
import time

# CREDENTIALS
AUTH0_SCOPE = 'openid offline_access profile MarketData ReadAccount Trade Crypto Matrix OptionSpreads'
REDIRECT_URI = 'http://localhost:3000/'
ACCOUNT = 'YOUR_ACCOUNT_ID_GOES_HERE'

with open('credentials.txt', 'r') as f:
    CLIENT_ID = f.readline().strip().split(':')[-1].strip()
    CLIENT_SECRET = f.readline().strip().split(':')[-1].strip()

print(CLIENT_ID)
print(CLIENT_SECRET)

# CONNECTIONS
connection = ct(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)

# Fetch the refresh code only once.
connection.fetch_refresh_token()

# Get access token and time of expiry.
token, time_to_expiry = connection.fetch_access_token()


while(True):
    # Validate and get new access token if expired.
    if (datetime.now() >= time_to_expiry):
        print('Token expired. Generating new token!.')
        token, time_to_expiry = connection.fetch_access_token()

    # Get current positions for the specified account.
    data = json.loads(connection.fetch_positions(ACCOUNT,True))['Positions']
    print(data)

    # NOTE: TradeStation API can provide 250 requests in 5 mins, that accounts to one request every 1.2 seconds.
    # We use 1.5 seconds delay before next request to make sure we do not exceed the limit.
    time.sleep(1.5)
