import discord
from discord.ext import commands
from Views.EventView import EventView, load_event_data
from dotenv import load_dotenv
import os
load_dotenv(dotenv_path='.env')
TOKEN = os.getenv('TOKEN')

intents = discord.Intents.default()
intents.message_content = True

class MyBot(commands.Bot):
    async def setup_hook(self):
        """在機器人啟動時加載所有 cogs"""
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                except Exception as e:
                    print(f"Failed to load {filename}: {e}")
                    
bot = MyBot(command_prefix='※',intents=intents)

@bot.command()
@commands.is_owner()
async def sync(ctx):
    """同步機器人命令"""
    await bot.tree.sync()
    await ctx.send("同步完成", silent=True)
    
@bot.command()
@commands.is_owner()
async def load(ctx, extension):
    """cog load"""
    await bot.load_extension(f"cogs.{extension}")
    await ctx.send(f"Loaded {extension} done.", silent=True)
    
@bot.command()
@commands.is_owner()
async def unload(ctx, extension):
    """cog unload"""
    await bot.unload_extension(f"cogs.{extension}")
    await ctx.send(f"Unloaded {extension} done.", silent=True)
    
@bot.command()
@commands.is_owner()
async def reload(ctx, extension):
    """cog reload"""
    await bot.reload_extension(f"cogs.{extension}")
    await ctx.send(f"Reloaded {extension} done.", silent=True)

@bot.event
async def on_ready():
    print(f"\033[35mLogged in as {bot.user}\033[0m")
    await bot.change_presence(activity=discord.Game(name="原神"))
    
    data = load_event_data()

    for message_id, info in data.items():
        try:
            channel_id = info.get("channel_id")
            participants = info.get("participants", [])

            channel = bot.get_channel(int(channel_id))  # 獲取頻道
            message = await channel.fetch_message(int(message_id))
            if message:
                # 恢復按鈕視圖
                view = EventView(message.id, channel.id)
                view.participants = set(participants)
                await message.edit(content=f"**誰會來({len(view.participants)}):** {', '.join(participants)}", view=view)
        except Exception as e:
            print(f"Error restoring message {message_id}: {e}")



if __name__ == "__main__":
    bot.run(TOKEN)