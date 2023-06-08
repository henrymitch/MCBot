import server
import discord
import os

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.content.lower().strip() == '!mc start':
        await message.channel.send("`[] Starting server...`")
        await server.start(message.channel.send)
        await message.channel.send("`[] Complete`")
        return
    
    if message.content.lower().strip() == '!mc stop':
        await message.channel.send("`[] Stopping server...`")
        await server.stop(message.channel.send)
        await message.channel.send("`[] Complete`")

client.run(os.getenv('DISCORD_TOKEN'))
