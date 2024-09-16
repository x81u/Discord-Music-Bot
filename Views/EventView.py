import discord
import json
import os

class EventView(discord.ui.View):
    def __init__(self, message_id=None, channel_id=None):
        super().__init__(timeout=None)  # 設置無限超時
        self.participants = set()  # 使用 set 來追蹤參加者
        self.message_id = message_id
        self.channel_id = channel_id

    @discord.ui.button(label="++", style=discord.ButtonStyle.blurple)
    async def vote(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 延遲回應，避免“此交互失敗”錯誤
        await interaction.response.defer()
        
        # 切換參加狀態
        if interaction.user.mention in self.participants:
            print(f'{interaction.user.mention} cancel the participation of the event "{self.message_id}"')
            self.participants.remove(interaction.user.mention)
        else:
            print(f'{interaction.user.mention} participate the event "{self.message_id}"')
            self.participants.add(interaction.user.mention)
        
        # 更新活動訊息
        participants_message = f"**誰會來({len(self.participants)}):** {', '.join(self.participants)}"
        await interaction.message.edit(content=participants_message)
        # 保存參加者列表
        save_event_data(self.message_id, self.channel_id, list(self.participants))

def save_event_data(message_id, channel_id, participants):
    """將按鈕狀態、頻道ID和原始消息存儲到文件中"""
    data = {}
    data_file = 'data/event_data.json'
    # 建立data資料夾
    os.makedirs('data', exist_ok=True)
    if os.path.exists(data_file):
        with open(data_file, "r") as f:
            data = json.load(f)

    data[str(message_id)] = {
        "channel_id": channel_id,
        "participants": participants
    }

    with open(data_file, "w") as f:
        json.dump(data, f, indent=4)  # 使用indent=4使JSON更可讀

def load_event_data():
    """從文件中讀取按鈕狀態"""
    data_file = 'data/event_data.json'
    if os.path.exists(data_file):
        with open(data_file, "r") as f:
            return json.load(f)
    return {}