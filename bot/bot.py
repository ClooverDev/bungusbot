# LIBS #
import discord
from discord import app_commands as appcmds
from discord.ext import commands as cmds
import os

from discord import interactions

import logging
from datetime import datetime as dt
from time import sleep as delay

import requests
import base64
import json
from dotenv import load_dotenv

import asyncio

# LOAD ##
load_dotenv()

GUILD=discord.Object(id=965060530446430268)
GUILD_TEST=discord.Object(id=1381695169115590716)

GITHUB_TOKEN=os.environ["GITHUB_TOKEN"]
REPO=os.environ["GITHUB_REPO"]
FILE_PATH=os.environ["GITHUB_FILE_PATH"]
API_URL=f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
token= os.environ['DISCORD_TKN']

HEADERS={
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "applications/vnd.github.v3+json"
}

## FUNCTIONS

# GET FILE
def get_file_sha():
    response = requests.get(API_URL, headers=HEADERS)
    if response.status_code == 200:
        return response.json()['sha']
    return None

# READ ALL VALUES WITHIN VALUES.JSON
def read_all_values():
    response = requests.get(API_URL, headers=HEADERS)
    if response.status_code == 200:
        content = base64.b64decode(response.json()['content']).decode()
        return json.loads(content)
    else:
        print(f"X Failed to read: {response.text}")
        return {}
    
# GET SPECIFIC VALUE FROM THE JSON FILE
def read_val(key):
    data = read_all_values()
    return data.get(key)

# UPDATE SPECIFIC VALUE FROM JSON FILE
def update_val(key, new_value):
    # Read current data and SHA
    response = requests.get(API_URL, headers=HEADERS)
    if response.status_code != 200:
        print(f"X Failed to read: {response.text}")
        return

    content_json = base64.b64decode(response.json()['content']).decode()
    data = json.loads(content_json)
    sha = response.json()['sha']

    # Update value
    data[key] = new_value

    # Encode new content
    new_content = base64.b64encode(json.dumps(data, indent=2).encode()).decode()

    # Push update
    update_response = requests.put(API_URL, headers=HEADERS, json={
        "message": f"Update '{key}' to {new_value}",
        "content": new_content,
        "sha": sha
    })

    if update_response.status_code in [200, 201]:
        print(f"V Updated '{key}' to {new_value}")
    else:
        print(f"X Failed to update: {update_response.text}")


##

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
ints=discord.Intents.default()
ints.message_content=True
ints.members=True

bung = cmds.Bot(command_prefix='b/', intents=ints)
pref="b/"
att = "attachment://"

__default_errors = {
    "PERM-ERROR" : "You cannot use this command: This command require higher permissions.",
}

### OTHERS ###
pingc=read_val("ping-count")
last_pinged=read_val("last-pinged")

# INITIALIZE
@bung.event
async def on_ready():
    print('We are so back.')
    
# COMMAND EVENT #
@bung.event
async def on_message(msg):
    await bung.change_presence(status=discord.Status.idle, activity=discord.Game("prefix: 'b/'"))
    guild=msg.guild
    author=msg.author
    
    if author==bung.user:
        return
    
    def check(command_name : str, locked : bool):
        if msg.content == pref+command_name:
            print("[CMD_USED]: "+command_name)
            
            if (locked):
                adm_roles = [
                    'role dev',
                ]
                
                for admin in adm_roles:
                    role=discord.utils.get(guild.roles, name=admin)
                    if role in author.roles:
                        return True
                    else:
                        return print("[!] User cannot use command.") # False
                        
            else:
                return True
        else:
            return False
        
    def check_full(command_name : str, locked : bool):
        if msg.content.startswith(pref+command_name):
            print("[CMD_USED]: "+command_name)
            
            if (locked):
                adm_roles = [
                    'role dev',
                ]
                
                for admin in adm_roles:
                    role=discord.utils.get(guild.roles, name=admin)
                    if role in author.roles:
                        return True
                    else:
                        print("[!] User cannot use command.") # False
                        return False
                        
            else:
                return True
        else:
            return False
        
    def return_error(err : str):
        return print(f"[ERROR] {err}")
        
    ############################################## COMMANDS ##############################################
    
    # PING
    if check("ping", True):
        try:
            get = dt.now().strftime("%I:%M:%S %p")
            
            global last_pinged
            
            global pingc
            pingc+=1
            update_val("ping-count",pingc)
            
            await msg.channel.send(f"Pinged at {get} | Last pinged at: {last_pinged}.\nThis bot was pinged over {pingc} times globally.")
            
            
            last_pinged=get
            update_val("last-pinged",last_pinged)
            
        except Exception as e:
            return_error(f"{e}")
    
    # LOGS #
    if check_full("logs", True):
        try:
            get_current_channel = msg.channel.id
            channel_to_log = bung.get_channel(1381734613973729401)
            
            get_args=msg.content.split()
            
            info={
                "title": "__default_title__",
                "log": "__default_log_body__",
                "icon": "https://clooverlandstudios.com/example.png",
                "date": "00.00.00",
                "version": "0.0.0",
            }
            
            for ind,word in enumerate(get_args):
                if ind>0:
                    if word != None:
                        if ind == 1: 
                            if word.startswith("https://"):
                                info['icon']=word
                            
                        if ind == 2: info["date"]=word
                        if ind == 3: info["version"]=word
                    
                    if ind > 3:
                        break;
            
            await msg.channel.send("Input your title.")
            
            # GET TITLE AND DECRIPTION
            def check(message):
                return message.author == msg.author and message.channel == msg.channel

            try:
                message = await bung.wait_for("message", check=check, timeout=60)
                info['title']=message.content
            except asyncio.TimeoutError:
                await msg.send("You took too long to respond.")
                
            await msg.channel.send("Input your description.")
            try:
                message = await bung.wait_for("message", check=check, timeout=60)
                info['log']=message.content
            except asyncio.TimeoutError:
                await msg.send("You took too long to respond.")
            
            # GENERATE EMBED
            log_emb = discord.Embed(
                color=discord.Color.random(),
                title=info["title"],
                description="`"+f"{info['date']}"+"`"+"\n"+info["log"],
            )
            log_emb.set_thumbnail(url=info["icon"])
            log_emb.set_footer(text=f"{info['version']}")
            
            await msg.channel.send(embed=log_emb)
            
        except Exception as err:
           return_error(err);
    
        
    ##########################################################################################################
        
    
    await bung.process_commands(msg)

#################################################### RUN TOKEN
bung.run(token, log_handler=handler, log_level=logging.DEBUG)