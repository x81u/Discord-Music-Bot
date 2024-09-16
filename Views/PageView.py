import discord

class PageView(discord.ui.View):
    def __init__(self, embeds, author, delete_after):
        super().__init__()
        self.embeds = embeds  # 用於存儲所有的 embeds
        self.page = 0  # 設置當前頁面索引
        self.author = author  # 保存指令發送者
        self.delete_after = delete_after
        
        # 初始化時禁用左翻頁按鈕（因為在第一頁）
        self.left_button.disabled = True
    
        # 如果只有一頁，禁用右翻頁按鈕
        if len(self.embeds) == 1:
            self.right_button.disabled = True
            
    # 左翻頁按鈕
    @discord.ui.button(label="上一頁", style=discord.ButtonStyle.blurple)
    async def left_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 檢查按鈕按下的人是否是原始指令的發送者
        if interaction.user != self.author:
            await interaction.response.send_message(f"{interaction.user.mention}別點了，只有指令輸入者能按按鈕==", ephemeral=True)
            return
        
        self.page -= 1  # 移動到上一頁
        self.update_buttons()  # 更新按鈕的啟用狀態

        # 刪除原來的消息並發送新消息
        await interaction.message.delete()
        await interaction.channel.send(embed=self.embeds[self.page], view=self, delete_after=self.delete_after, silent=True)

    # 右翻頁按鈕
    @discord.ui.button(label="下一頁", style=discord.ButtonStyle.blurple)
    async def right_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 檢查按鈕按下的人是否是原始指令的發送者
        if interaction.user != self.author:
            await interaction.response.send_message(f"{interaction.user.mention}別點了，只有指令輸入者能按按鈕==", ephemeral=True)
            return
        
        self.page += 1  # 移動到下一頁
        self.update_buttons()  # 更新按鈕的啟用狀態

        # 刪除原來的消息並發送新消息
        await interaction.message.delete()
        await interaction.channel.send(embed=self.embeds[self.page], view=self, delete_after=self.delete_after, silent=True)

    def update_buttons(self):
        # 當在第一頁時，禁用左翻頁按鈕
        self.left_button.disabled = self.page == 0
        # 當在最後一頁時，禁用右翻頁按鈕
        self.right_button.disabled = self.page == len(self.embeds) - 1
        