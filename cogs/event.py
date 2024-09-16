import discord
from discord.ext import commands
from Views.EventView import EventView, save_event_data

class Event(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    
    @commands.hybrid_command()
    async def create_event(self, ctx, 標題, 時間, 地點, *, 要幹嘛):
        """建立活動訊息"""
        # 建立 Embed 物件
        embed = discord.Embed(
            title=f"🎉 {標題}",
            description="**要的點按鈕++**",
            color=discord.Color.purple()  # 設定嵌入的顏色
        )

        # 添加嵌入字段
        embed.add_field(name="📅 時間", value=f"* {時間}", inline=False)
        embed.add_field(name="📍 地點", value=f"* {地點}", inline=False)
        embed.add_field(name="💬 要幹嘛", value=f"* {要幹嘛}", inline=False)
        embed.set_footer(text="按鈕點不了就是機器人沒上線")
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
        embed.set_thumbnail(url=ctx.author.avatar.url)
        #embed.set_image(url="https://imgur.com/QEIv47a")

        
        # 創建按鈕視圖
        view = EventView()

        # 發送活動消息並附加按鈕
        message = await ctx.send(embed=embed, view=view)
        view.message_id = message.id
        view.channel_id = message.channel.id

        # 保存事件的空參加者列表和原始消息
        save_event_data(message.id, message.channel.id, [])
        

async def setup(bot):
    await bot.add_cog(Event(bot))