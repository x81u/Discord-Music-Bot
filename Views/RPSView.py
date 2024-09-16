import discord

class RockPaperScissorsView(discord.ui.View):
    def __init__(self, challenger, opponent):
        super().__init__(timeout=120)  # 設置按鈕的超時時間
        self.challenger = challenger
        self.opponent = opponent
        self.choices = {}  # 用來記錄雙方的選擇

    @discord.ui.button(label="石頭", style=discord.ButtonStyle.primary)
    async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.make_choice(interaction, "石頭")

    @discord.ui.button(label="剪刀", style=discord.ButtonStyle.primary)
    async def scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.make_choice(interaction, "剪刀")

    @discord.ui.button(label="布", style=discord.ButtonStyle.primary)
    async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.make_choice(interaction, "布")

    async def make_choice(self, interaction: discord.Interaction, choice: str):
        """處理用戶選擇並決定結果"""
        await interaction.response.defer(ephemeral=True)
        if interaction.user.id not in [self.challenger.id, self.opponent.id]:
            print(f"{interaction.user.mention} 只有挑戰者和被挑戰者能夠使用按鈕。")
            await interaction.followup.send(f"{interaction.user.mention} 只有挑戰者和被挑戰者能夠使用按鈕。", ephemeral=True)
            return
        
        self.choices[interaction.user.id] = choice
        await interaction.followup.send(f"{interaction.user.mention} 選擇了 {choice}", ephemeral=True)

        # 當兩個用戶都做出了選擇時，決定勝者
        if len(self.choices) == 2:
            await self.declare_winner(interaction)

    async def declare_winner(self, interaction: discord.Interaction):
        challenger_choice = self.choices[self.challenger.id]
        opponent_choice = self.choices[self.opponent.id]
        result_message = f"{self.challenger.mention} 選擇了 {challenger_choice}，{self.opponent.mention} 選擇了 {opponent_choice}。\n"

        if challenger_choice == opponent_choice:
            result_message += "這是一場平局。"
        elif (challenger_choice == "石頭" and opponent_choice == "剪刀") or \
             (challenger_choice == "剪刀" and opponent_choice == "布") or \
             (challenger_choice == "布" and opponent_choice == "石頭"):
            result_message += f"{self.challenger.mention} 贏了。"
        else:
            result_message += f"{self.opponent.mention} 贏了。"
        
        await interaction.followup.send(result_message)

        # 停用所有按鈕
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True

        # 編輯原消息以停用按鈕
        await interaction.message.edit(view=self)
        self.stop()  # 停止視圖，關閉按鈕