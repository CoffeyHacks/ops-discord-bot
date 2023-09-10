import os
import json
import discord
from discord.ext import commands, tasks
from discord_slash import SlashCommand
import requests
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPS_USERNAME = os.getenv("OPS_USERNAME")
OPS_PASSWORD = os.getenv("OPS_PASSWORD")
OPS_TOKEN = os.getenv("OPS_TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)
slash = SlashCommand(bot, sync_commands=True)

def get_new_ops_token():
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
    if 'phonenumber' in data:
        return "https://api.openpeoplesearch.com/api/v1/Consumer/PhoneSearch"
    elif 'emailaddress' in data:
        return "https://api.openpeoplesearch.com/api/v1/Consumer/EmailAddressSearch"
    elif 'address' in data:
        return "https://api.openpeoplesearch.com/api/v1/Consumer/AddressSearch"
    elif 'firstname' in data and 'lastname' in data:
        if 'dob' in data:
            return "https://api.openpeoplesearch.com/api/v1/Consumer/NameDOBSearch"
        else:
            return "https://api.openpeoplesearch.com/api/v1/Consumer/NameSearch"
    else:
        return None

@tasks.loop(hours=6.5)
async def renew_ops_token():
    global OPS_TOKEN
    new_token = get_new_ops_token()
    if new_token:
        OPS_TOKEN = new_token
        print("OPS Token successfully renewed!")
    else:
        print("Failed to renew the OPS token. Trying again in 6.5 hours.")

@slash.slash(
    name="search",
    description="Perform a search with the given parameters.",
    options=[
        {
            "name": "firstname",
            "description": "First Name of the person you're looking for.",
            "type": 3,
            "required": False
        },
        {
            "name": "lastname",
            "description": "Last Name of the person you're looking for.",
            "type": 3,
            "required": False
        },
        {
            "name": "dob",
            "description": "Date of Birth of the person you're looking for (in MMDDYYYY format).",
            "type": 3,
            "required": False
        },
        {
            "name": "phonenumber",
            "description": "Phone number of the person you're looking for.",
            "type": 3,
            "required": False
        },
        {
            "name": "emailaddress",
            "description": "Email address of the person you're looking for.",
            "type": 3,
            "required": False
        },
        {
            "name": "address",
            "description": "Address of the person you're looking for.",
            "type": 3,
            "required": False
        }
    ]
)
async def _search(ctx, firstname=None, lastname=None, dob=None, phonenumber=None, emailaddress=None, address=None):
    data = {
        "firstname": firstname,
        "lastname": lastname,
        "dob": dob,
        "phonenumber": phonenumber,
        "emailaddress": emailaddress,
        "address": address
    }
    data = {k: v for k, v in data.items() if v}
    
    endpoint_url = get_ops_endpoint(data)
    if not endpoint_url:
        await ctx.send(content="Invalid search parameters. Please check your query and try again.")
        return

    headers = {
        'Authorization': f'Bearer {OPS_TOKEN}',
        'Content-Type': 'application/json',
    }

    response = requests.post(endpoint_url, headers=headers, json=data, timeout=120)

    if response.status_code == 200:
        try:
            results = response.json()
            if 'data' in results:
                await ctx.send(content=str(results['data']))
            else:
                await ctx.send(content="No data found.")
        except json.JSONDecodeError:
            await ctx.send(content="Error occurred while processing server response. Please try again later.")
    else:
        await ctx.send(content=f"Error occurred while searching. Please try again. (Error: {response.status_code})")

bot.run(DISCORD_TOKEN)
