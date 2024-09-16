import discord
from discord.ext import commands
from Views.RPSView import RockPaperScissorsView

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}  # 用來追蹤活躍的遊戲
        self.delete_after = 30

    @commands.hybrid_command()
    async def rps(self, ctx, opponent: discord.User):
        """向[opponent]發起一個猜拳挑戰"""
        challenger = ctx.author
        if opponent == challenger:
            await ctx.send("你不能向自己挑戰。", delete_after=self.delete_after, ephemeral=True)
            return
        
        if ctx.channel.id in self.active_games:
            await ctx.send("已經有一場活躍的遊戲正在進行，請等待結束後再發起挑戰。", delete_after=self.delete_after, ephemeral=True)
            return

        view = RockPaperScissorsView(challenger, opponent)
        self.active_games[ctx.channel.id] = view  # 記錄活躍遊戲
        await ctx.send(f"{opponent.mention}, 你被 {challenger.mention} 挑戰了一場猜拳。", view=view)
        await view.wait()  # 等待遊戲結束
        del self.active_games[ctx.channel.id]  # 移除遊戲

async def setup(bot):
    await bot.add_cog(Games(bot))