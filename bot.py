import os
import discord
import json  # <-- Import this to handle JSON errors
from discord.ext import commands, tasks
import requests
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPS_USERNAME = os.getenv("OPS_USERNAME")
OPS_PASSWORD = os.getenv("OPS_PASSWORD")
OPS_TOKEN = os.getenv("OPS_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.presences = True  # This enables the Presence Intent
intents.members = True    # This enables the Server Members Intent
bot = commands.Bot(command_prefix="!", intents=intents)

def get_new_ops_token():
    """Retrieve a new authentication token from OPS."""
    auth_data = {
        'username': OPS_USERNAME,
        'password': OPS_PASSWORD
    }
    response = requests.post("https://api.openpeoplesearch.com/api/v1/User/authenticate", json=auth_data, timeout=120)
    if response.status_code == 200:
        token = response.json().get("token")
        print("Success!")
        return token
    else:
        print("Error retrieving OPS API Token")
        return None

def get_ops_endpoint(data):
    if 'phoneNumber' in data:
        return "https://api.openpeoplesearch.com/api/v1/Consumer/PhoneSearch"
    elif 'emailAddress' in data:
        return "https://api.openpeoplesearch.com/api/v1/Consumer/EmailAddressSearch"
    elif 'firstName' in data and 'lastName' in data and 'address' not in data and 'dob' not in data:
        return "https://api.openpeoplesearch.com/api/v1/Consumer/NameSearch"
    elif 'firstName' in data and 'lastName' in data and 'address' in data:
        return "https://api.openpeoplesearch.com/api/v1/Consumer/NameAddressSearch"
    elif 'firstName' in data and 'lastName' in data and 'dob' in data:
        return "https://api.openpeoplesearch.com/api/v1/Consumer/NameDOBSearch"
    elif 'businessName' in data:
        return "https://api.openpeoplesearch.com/api/v1/Consumer/BusinessSearch"
    elif 'address' in data:
        return "https://api.openpeoplesearch.com/api/v1/Consumer/AddressSearch"
    elif 'poBox' in data:
        return "https://api.openpeoplesearch.com/api/v1/Consumer/PoBoxSearch"
    else:
        return None

@tasks.loop(hours=6.5)
async def renew_ops_token():
    """Renew the OPS token at regular intervals."""
    global OPS_TOKEN
    new_token = get_new_ops_token()
    if new_token:
        OPS_TOKEN = new_token
        print("OPS Token successfully renewed!")
    else:
        print("Failed to renew the OPS token. Trying again in 6.5 hours.")

@bot.command(name='search')
async def search(ctx, first_name=None, last_name=None, middle_name=None, dob=None, address=None, phoneNumber=None, emailAddress=None, businessName=None, poBox=None):
    """Search for data in OPS using the provided parameters."""
    data = {
        "firstName": first_name,
        "lastName": last_name,
        "middleName": middle_name,
        "dob": dob,
        "address": address,
        "phoneNumber": phoneNumber,
        "emailAddress": emailAddress,
        "businessName": businessName,
        "poBox": poBox
    }

    # Remove None values to refine the search payload
    data = {k: v for k, v in data.items() if v}

    endpoint_url = get_ops_endpoint(data)
    if not endpoint_url:
        await ctx.send("Invalid search parameters. Please check your query and try again.")
        return

    headers = {
        'Authorization': f'Bearer {OPS_TOKEN}',
        'Content-Type': 'application/json',
    }

    response = requests.post(endpoint_url, headers=headers, json=data, timeout=120)

    # Check if the response content type is JSON
    content_type = response.headers.get("Content-Type", "")
    if "application/json" not in content_type:
    # handle the error

        await ctx.send("Received an unexpected response from the server. Please try again later.")
        return

    try:
        results = response.json()
    except json.JSONDecodeError:
        await ctx.send("Error occurred while processing server response. Please try again later.")
        return

    if response.status_code == 200 and 'data' in results:
        await ctx.send(str(results['data']))
    else:
        await ctx.send("Error occurred while searching. Please try again.")

bot.run(DISCORD_TOKEN)

