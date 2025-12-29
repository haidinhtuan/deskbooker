import os
import json
import requests
from deskbooker.auth import get_access_token
from dotenv import load_dotenv

load_dotenv()

def check_limits():
    token_key = os.environ["TOKEN_KEY"]
    refresh_token = os.environ["REFRESH_TOKEN"]
    workspace_id = os.environ["WORKSPACE_ID"]
    
    access_token = get_access_token(token_key, refresh_token)
    
    # URL to fetch user/workspace config
    # The bookings endpoint returns workspace settings in the 'bookings' list structure or similar
    # But usually, there is a dedicated endpoint for settings or we can check the 'settings' block in a booking response
    
    url = f"https://api.deskbird.app/v1.1/user/bookings?upcoming=true&limit=1"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(url, headers=headers)
    data = response.json()
    # print(json.dumps(data, indent=2)) 
    
    # Try to find results either at top level or inside 'data'
    results = data.get("results")
    if not results and "data" in data:
         # Maybe it's inside data?
         # print(data['data']) 
         pass
         
    # Let's just inspect what we have based on the output 'dict_keys(['success', 'data'])'
    print(json.dumps(data, indent=2))

if __name__ == "__main__":
    check_limits()
