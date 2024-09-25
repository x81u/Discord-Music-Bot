import discord
from discord.ext import commands
from discord import app_commands
from discord import FFmpegPCMAudio
from yt_dlp import YoutubeDL
from Views.PageView import PageView
from pydub import AudioSegment
import asyncio
import concurrent.futures
import random
import json
import os
import re

async def delete_after_delay(interaction: discord.Interaction, delay: int):
    """在指定的延遲後刪除回應的訊息。"""
    await asyncio.sleep(delay)
    try:
        message = await interaction.original_response()
        await message.delete()
    except discord.errors.NotFound:
        pass  # 忽略已經被刪除的消息

def extract_video_id(url):
    """提取 url 的唯一 ID"""
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(pattern, url)
    return match.group(1) if match else url
    
def get_file_path(video_id, title=None):
    """生成音樂文件的存儲路徑"""
    if title:
        title = title.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')  # 避免非法字符
        return f"downloads/{video_id}+{title}.mp3"
    else:
        # 嘗試匹配已存在的文件名稱（使用文件夾列出所有文件）
        os.makedirs('downloads', exist_ok=True)
        for file_name in os.listdir('downloads'):
            if file_name.startswith(f"{video_id}+") and file_name.endswith(".mp3"):
                return f"downloads/{file_name}"
        return None
        
def youtube_dl_process(playlist_url, ydl_opts, legnth):
    """處理 YoutubeDL 播放清單請求並格式化資訊"""
    try:
        # 使用 yt-dlp 提取播放清單中的所有影片 URL
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(playlist_url, download=False)
            
            playlist_title = info_dict.get('title', '').lower()
            songs_count = len(info_dict['entries'])
            print(f'\033[33mFind {songs_count} songs.\033[0m')
            if 'mix - ' in playlist_title:
                print('\033[33mIt is a auto-generated playlist.\033[0m')
                if legnth == None:
                    legnth = 25
                video_urls = [video['url'] for video in info_dict['entries'][:legnth]]
            else:
                if legnth == None:
                    video_urls = [video['url'] for video in info_dict['entries']]
                else:
                    video_urls = [video['url'] for video in info_dict['entries'][:legnth]]
                    
        # 處理並獲取格式化的音樂資訊
        formatted_infos = fetch_infos_concurrently_sync(video_urls)
        
        return formatted_infos

    except Exception as e:
        # 錯誤訊息以str形式回傳，以防型態不可分割問題
        return f"{e}"
    
def fetch_infos_concurrently_sync(video_urls):
    """多執行緒加速獲取多個音樂資訊"""
    def fetch_info(url):
        video_id = extract_video_id(url)
        return fetch_detailed_music_info(video_id, noerror=True)  # 使用同步函數 fetch_detailed_music_info_noerror 取得資訊

    # 使用多執行緒來加速
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(fetch_info, video_urls))

    # 格式化結果資訊為{video_id}+{title}
    formatted_infos = [f"{info['id']}+{info['title']}" for info in results if info]
    return formatted_infos
    
def download_from_youtube(video_id):
    """獲取音樂的詳細資訊，如標題、上傳者和縮圖等，並下載音樂"""
    # 設定下載選項
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(id)s+%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True
    }
    
    # 建立downloads資料夾
    os.makedirs('downloads', exist_ok=True)
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_id, download=True)
    except Exception as e:
        # 錯誤訊息以str形式回傳，以防型態不可分割問題
        return f"{e}"
    
    # 原始文件名和路徑
    original_file_path = get_file_path(info['id'])
    
    # 處理文件名
    new_file_path = get_file_path(video_id, info['title'])

    # 確保文件名不會重複
    if original_file_path != new_file_path:
        print(f'\033[36mRenaming file_path from "{original_file_path}" to "{new_file_path}"\033[0m')
        os.rename(original_file_path, new_file_path)
        
    song_info = {
        'id': info.get('id'),
        'title': info.get('title'),
        'uploader': info.get('uploader'),
        'thumbnail': info.get('thumbnail'),
        'duration': info.get('duration'),
        'url': info.get('webpage_url'),
        'view_count': info.get('view_count'),
        'like_count': info.get('like_count'),
        'uploader_url': info.get('uploader_url')
    }
    
    print(f"\033[33mReturn the downloaded info of {info['title']}\033[0m")
    return new_file_path, song_info

def fetch_detailed_music_info(video_id, noerror=False):
    """獲取音樂的詳細資訊，如標題、上傳者和縮圖等。"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_id, download=False)
    except Exception as e:
        if noerror:
            return
        else:
            # 錯誤訊息以str形式回傳，以防型態不可分割問題
            return f"{e}"
    
    # 返回詳細資訊，例如標題、上傳者和縮圖
    print(f"\033[33mReturn the info of {info['title']}\033[0m")
    return {
        'id': info.get('id'),
        'title': info.get('title'),
        'uploader': info.get('uploader'),
        'thumbnail': info.get('thumbnail'),
        'duration': info.get('duration'),
        'url': info.get('webpage_url'),
        'view_count': info.get('view_count'),
        'like_count': info.get('like_count'),
        'uploader_url': info.get('uploader_url')
    }

def truncate_song_title(title, max_length=50):
    """截斷歌名以不超過max_length個字"""
    if len(title) > max_length:
        # 如果超過最大字數，截斷並加上 "..."
        truncated_title = title[:max_length - 3] + '...'
        return truncated_title
    else:
        return title

def calculate_average_volume(file_path):
    """計算一首歌的平均分貝"""
    # 讀取音樂
    audio = AudioSegment.from_file(file_path)

    # 計算的音樂的分貝 (dBFS)
    avg_volume = audio.dBFS

    return avg_volume
        
class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue_dict = {}  # 音樂佇列
        self.current_song_info = {}  # 當前播放音樂資訊
        self.music_config = {}
        
    def load_music_config(self):
        """讀取music_config的資料"""
        music_config_file = 'data/music_config.json'
        if os.path.exists(music_config_file):
            with open('data/music_config.json', 'r') as f:
                return json.load(f)
        return {}

    def save_music_config(self):
        """保存當前配置到music_config"""
        music_config_file = 'data/music_config.json'
        # 建立data資料夾
        os.makedirs('data', exist_ok=True)
        with open(music_config_file, 'w') as f:
            json.dump(self.music_config, f, indent=4)

    def get_music_config(self, guild_id):
        """獲取當前music_config"""
        # 預設為delete_after: 30, music_volume: -30
        return self.music_config.get(guild_id, {"delete_after": 30, "music_volume": -30}) 

    def load_playlists(self):
        """讀取user_playlist_file的資料"""
        user_playlist_file  = 'data/user_playlists.json'
        if os.path.exists(user_playlist_file):
            with open(user_playlist_file, 'r') as f:
                return json.load(f)
        return {}

    def save_playlists(self, playlists):
        """保存playlist到user_playlist_file"""
        user_playlist_file  = 'data/user_playlists.json'
        # 建立data資料夾
        os.makedirs('data', exist_ok=True)
        with open(user_playlist_file, 'w') as f:
            json.dump(playlists, f, indent=4)
                
    def append_queue_dict(self, guild_id, formatted_info):
        """將歌加入queue"""
        if guild_id not in self.queue_dict:
            self.queue_dict[guild_id] = []
        self.queue_dict[guild_id].append(formatted_info)
        
    def get_queue_len(self, guild_id):
        """得到目前queue長度"""
        return len(self.queue_dict.get(guild_id, {}))
    
    def get_current_song_info(self, guild_id):
        """獲取當前歌曲資訊"""
        return self.current_song_info.get(guild_id, None)
        
    async def play_next(self, interaction: discord.Interaction):
        """播放佇列中的下一首音樂"""
        guild_id = str(interaction.guild.id)
        guild_config = self.get_music_config(guild_id)
        # 當佇列沒有音樂時
        if self.get_queue_len(guild_id) == 0:
            if self.get_current_song_info(guild_id):
                del self.current_song_info[guild_id]
            # 切換狀態回非播放音樂狀態
            if len(self.current_song_info) != 0:
                text = f"正在 {len(self.current_song_info)} 個伺服器播放音樂"
                await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=text))
            else:
                await self.bot.change_presence(activity=discord.Game(name="原神"))
                
            await interaction.channel.send("佇列中沒有更多歌曲。", silent=True, delete_after=guild_config['delete_after'])
            return

        # 從佇列中取得下一首歌曲並提取 {video_id}+{title}
        formatted_info = self.queue_dict[guild_id].pop(0)
        video_id, title = formatted_info.split("+", 1)

        # 嘗試取得已存在的文件路徑
        file_path = get_file_path(video_id)

        # 如果文件不存在，則下載並儲存
        if not file_path:
            # 下載音樂並得到詳細的音樂資訊
            # 使用 ProcessPoolExecutor 來執行多進程操作，來降低IO對主進程影響
            loop = asyncio.get_running_loop()
            with concurrent.futures.ProcessPoolExecutor() as executor:
                future = loop.run_in_executor(executor, download_from_youtube, video_id)
                info = await future
            
            # 錯誤訊息以str形式回傳，以防型態不可分割問題
            if type(info) is str:
                await interaction.channel.send(f"無法從 YouTube 匯入歌曲：{info}", silent=True, delete_after=guild_config['delete_after'])
                return
            
            file_path, self.current_song_info[guild_id] = info
        else:
            # 獲取詳細的音樂資訊，但不下載
            # 使用 ProcessPoolExecutor 來執行多進程操作，來降低IO對主進程影響
            loop = asyncio.get_running_loop()
            with concurrent.futures.ProcessPoolExecutor() as executor:
                future = loop.run_in_executor(executor, fetch_detailed_music_info, video_id)
                info = await future
            
            # 錯誤訊息以str形式回傳，以防型態不可分割問題
            if type(info) is str:
                await interaction.channel.send(f"無法從 YouTube 匯入歌曲：{info}", silent=True, delete_after=guild_config['delete_after'])
                return
            
            self.current_song_info[guild_id] = await future
        print(f'\033[32mPlaying {title}\033[0m')
        # 根據正在播放音樂的伺服器數量更改狀態
        text = f"正在 {len(self.current_song_info)} 個伺服器播放音樂"
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=text))
        
        # 計算音樂的平均音量
        avg_volume = calculate_average_volume(file_path)
        # 調整音量 (將平均音量調整為music_volume dBFS)
        volume_adjustment = guild_config['music_volume'] - avg_volume
        
        # 播放音樂文件
        source = FFmpegPCMAudio(file_path, options=f"-filter:a 'volume={volume_adjustment}dB'")  # 設定音量過濾器
        voice_client = interaction.guild.voice_client
        # 確認機器人在語音頻道中
        if voice_client and voice_client.is_connected():
            voice_client.play(source, after=lambda e: self.bot.loop.create_task(self.on_music_end(interaction, e)))
            embed = self.create_current_embed(guild_id)
            await interaction.channel.send(embed=embed, delete_after=guild_config['delete_after'], silent=True)
        else:
            if self.get_current_song_info(guild_id):
                del self.current_song_info[guild_id]
            # 切換狀態回非播放音樂狀態
            if len(self.current_song_info) != 0:
                text = f"正在 {len(self.current_song_info)} 個伺服器播放音樂"
                await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=text))
            else:
                await self.bot.change_presence(activity=discord.Game(name="原神"))
            await interaction.channel.send("無法播放音樂，語音客戶端未連接到語音頻道。", silent=True, delete_after=guild_config['delete_after'])

    async def on_music_end(self, interaction, error):
        """當音樂結束播放時的回調函數"""
        if error:
            print(f"\033[31m播放錯誤: {error}\033[0m")
        
        await self.play_next(interaction)
        
    @app_commands.command(name="set_config", description="設定音樂機器人的配置")
    @app_commands.describe(delete_after="設置刪除訊息延遲時間(範圍10~600 秒)", music_volume="設置音量大小(範圍-60~0 dB)")
    async def set_config(self, interaction: discord.Interaction, delete_after: int = None, music_volume: int = None):
        """設置音樂機器人的配置"""
        guild_id = str(interaction.guild.id)
        guild_config = self.get_music_config(guild_id)
        # 檢查範圍
        if delete_after is not None:
            if 10 <= delete_after <= 600:
                guild_config["delete_after"] = delete_after
            else:
                await interaction.response.send_message("`delete_after` 的範圍必須在 10 到 600 秒之間。", ephemeral=True)
                return
        
        if music_volume is not None:
            if -60 <= music_volume <= 0:
                guild_config["music_volume"] = music_volume
            else:
                await interaction.response.send_message("`music_volume` 的範圍必須在 -60 到 0 分貝之間。", ephemeral=True)
                return

        # 更新配置並保存
        self.music_config[str(guild_id)] = guild_config
        self.save_music_config()
        
        await interaction.response.send_message(
            "配置已更新：\n訊息刪除延遲: {} 秒\n音樂音量: {} dB".format(guild_config["delete_after"],guild_config["music_volume"]), ephemeral=True
        )
        
    @app_commands.command(name="join", description="將機器人加到你現在的頻道")
    async def join(self, interaction: discord.Interaction):
        """將機器人加到你現在的頻道"""
        guild_id = str(interaction.guild.id)
        guild_config = self.get_music_config(guild_id)
        if interaction.user.voice:
            channel = interaction.user.voice.channel
            if interaction.guild.voice_client is None:
                await channel.connect()
            elif interaction.guild.voice_client.channel != channel:
                await interaction.guild.voice_client.move_to(channel)
            await interaction.response.send_message("機器人已加入頻道。", ephemeral=True)
            # 若是機器人因為某原因而離開頻道(被踢掉或/leave)，可能queue_dict還有殘留音樂
            if self.get_queue_len(guild_id) != 0:
                await self.play_next(interaction)
        else:
            await interaction.response.send_message("你需要在語音頻道中！", ephemeral=True)
        await delete_after_delay(interaction, guild_config['delete_after'])

    @app_commands.command(name="leave", description="使機器人離開當前頻道")
    async def leave(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        guild_config = self.get_music_config(guild_id)
        """使機器人離開當前頻道"""
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message("機器人已離開頻道。", ephemeral=True)
        else:
            await interaction.response.send_message("機器人不在任何語音頻道中。", ephemeral=True)
        await delete_after_delay(interaction, guild_config['delete_after'])

    @app_commands.command(name="play", description="播放音樂或將音樂加入佇列")
    @app_commands.describe(url="'一首'歌曲的網址")
    async def play(self, interaction: discord.Interaction, url: str):
        """播放音樂或將音樂加入佇列"""
        guild_id = str(interaction.guild.id)
        guild_config = self.get_music_config(guild_id)
        # 檢查使用者是否在語音頻道
        if interaction.user.voice is None:
            await interaction.response.send_message("請先加入一個語音頻道！", ephemeral=True, silent=True)
            await delete_after_delay(interaction, guild_config['delete_after'])
            return

        # 取得語音頻道並連接
        voice_channel = interaction.user.voice.channel
        if interaction.guild.voice_client is None:
            await voice_channel.connect()
        elif interaction.guild.voice_client.channel != voice_channel:
            await interaction.guild.voice_client.move_to(voice_channel)

        await interaction.response.defer()
        # 添加音樂到佇列
        video_id = extract_video_id(url)
        # 使用 ProcessPoolExecutor 來執行多進程操作，來降低IO對主進程影響
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as executor:
            future = loop.run_in_executor(executor, fetch_detailed_music_info, video_id)
            info = await future
            
        # 錯誤訊息以str形式回傳，以防型態不可分割問題
        if type(info) is str:
            await interaction.followup.send(f"無法從 YouTube 匯入歌曲：{info}", silent=True)
            await delete_after_delay(interaction, guild_config['delete_after'])
            return

        # 將 {video_id}+{title} 加入佇列
        formatted_info = f"{info['id']}+{info['title']}"
        self.append_queue_dict(guild_id, formatted_info)
        await interaction.followup.send(f"歌曲已加入佇列。當前佇列長度：{self.get_queue_len(guild_id)}", silent=True)

        # 如果目前沒有音樂播放，開始播放佇列
        if not self.get_current_song_info(guild_id):
            await self.play_next(interaction)
        
        await delete_after_delay(interaction, guild_config['delete_after'])

    def create_current_embed(self, guild_id):
        """回傳當前播放的音樂embed(play_next, current)"""
        guild_config = self.get_music_config(guild_id)
        # 創建 Discord embed
        song_info = self.get_current_song_info(guild_id)
        embed = discord.Embed(
            title="🎵 現在播放🎵",
            description=f"🎶 [{song_info['title']}]({song_info['url']}) 🎶",
            color=discord.Color.blue()
        )
        
        embed.set_image(url=song_info['thumbnail'])
        
        # YouTube 自動建立的音樂沒有上傳者連結
        if song_info['uploader_url'] != None:
            embed.add_field(name="🎤 上傳者", value=f"**[{song_info['uploader']}]({song_info['uploader_url']})**", inline=True)
        else:
            embed.add_field(name="🎤 上傳者", value=f"**{song_info['uploader']}**", inline=True)
        embed.add_field(name="⏰ 時長", value=f"**{song_info['duration'] // 60}:{song_info['duration'] % 60:02d}**", inline=True)
        embed.add_field(name="🔥 播放量", value=f"**{song_info['view_count']:,}**", inline=True)
        embed.add_field(name="👍 按讚數", value=f"**{song_info['like_count']:,}**", inline=True)
        
        embed.set_footer(text=f"資訊只會展示{guild_config['delete_after']}秒\n輸入/current 可重新展示")
        
        return embed
        
    @app_commands.command(name="current", description="顯示當前播放的音樂")
    async def current(self, interaction: discord.Interaction):
        """顯示當前播放的音樂"""
        guild_id = str(interaction.guild.id)
        guild_config = self.get_music_config(guild_id)
        if self.get_current_song_info(guild_id):
            embed = self.create_current_embed(guild_id)
            await interaction.response.send_message(embed=embed, delete_after=guild_config['delete_after'], silent=True)
        else:
            await interaction.response.send_message("目前沒有正在播放的音樂。", delete_after=guild_config['delete_after'], silent=True)
        await delete_after_delay(interaction, guild_config['delete_after'])

    def queue_embeds(self, interaction: discord.Interaction):
        """回傳queue中的所有歌曲之embed集合(queue_show, queue_shuffle)"""
        embeds = []  # 儲存所有嵌入的列表
        chunk_size = 10  # 每個嵌入中顯示的最大歌曲數量
        
        guild_id = str(interaction.guild.id)
        # 將佇列內容分批處理
        for i in range(0, self.get_queue_len(guild_id), chunk_size):
            embed = discord.Embed(
                title="🎵 當前音樂佇列",
                description=f"🎶 當前佇列中的音樂 (第 {i // chunk_size + 1} 頁 / 共 {(self.get_queue_len(guild_id) + chunk_size - 1) // chunk_size} 頁)：",
                color=discord.Color.blue()
            )

            # 添加這批次的歌曲到嵌入
            song_list = [f"{j + 1}. [{truncate_song_title(song.split('+', 1)[1])}](https://youtu.be/{song.split('+', 1)[0]})" for j, song in enumerate(self.queue_dict[guild_id][i:i + chunk_size], start=i)]
            playlist_content = "\n".join(song_list)
            embed.add_field(name="歌曲列表", value=playlist_content, inline=False)

            embeds.append(embed)  # 將此嵌入加入到列表中
            
        return embeds
    
    @app_commands.command(name="queue_show", description="顯示當前佇列中的所有音樂")
    async def queue_show(self, interaction: discord.Interaction):
        """顯示當前佇列中的所有音樂"""
        guild_id = str(interaction.guild.id)
        guild_config = self.get_music_config(guild_id)
        if self.get_queue_len(guild_id) > 0:
            embeds = self.queue_embeds(interaction)
            # 發送嵌入
            view = PageView(embeds, interaction.user, guild_config['delete_after'])
            await interaction.response.send_message(embed=embeds[0], view=view, silent=True)
        else:
            await interaction.response.send_message("目前佇列中沒有音樂。", silent=True)
        await delete_after_delay(interaction, guild_config['delete_after'])
            
    @app_commands.command(name="queue_shuffle", description="打亂目前佇列中的音樂順序")
    async def queue_shuffle(self, interaction: discord.Interaction):
        """打亂目前佇列中的音樂順序"""
        guild_id = str(interaction.guild.id)
        guild_config = self.get_music_config(guild_id)
        if self.get_queue_len(guild_id) > 0:
            random.shuffle(self.queue_dict[guild_id])
            await interaction.response.send_message(f"已打亂目前佇列中的音樂順序。", silent=True)
            # 發送嵌入
            embeds = self.queue_embeds(interaction)
            view = PageView(embeds, interaction.user, guild_config['delete_after'])
            await interaction.channel.send(embed=embeds[0], view=view, silent=True, delete_after=guild_config['delete_after'])
        else:
            await interaction.response.send_message("目前佇列中沒有音樂。", silent=True)
        await delete_after_delay(interaction, guild_config['delete_after'])

    @app_commands.command(name="skip", description="跳過當前歌曲，播放佇列中的下一首歌曲")
    async def skip(self, interaction: discord.Interaction):
        """跳過當前歌曲，播放佇列中的下一首歌曲"""
        guild_id = str(interaction.guild.id)
        guild_config = self.get_music_config(guild_id)
        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.stop()
            await interaction.response.send_message("跳過當前歌曲。", silent=True)
        else:
            await interaction.response.send_message("目前沒有播放的音樂。", silent=True)
        await delete_after_delay(interaction, guild_config['delete_after'])
        
    @app_commands.command(name="pause", description="暫停音樂")
    async def pause(self, interaction: discord.Interaction):
        """暫停音樂"""
        guild_id = str(interaction.guild.id)
        guild_config = self.get_music_config(guild_id)
        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.pause()
            await interaction.response.send_message("音樂已暫停。", silent=True)
        else:
            await interaction.response.send_message("目前沒有音樂播放。", silent=True)
        await delete_after_delay(interaction, guild_config['delete_after'])

    @app_commands.command(name="resume", description="恢復播放音樂")
    async def resume(self, interaction: discord.Interaction):
        """恢復播放音樂"""
        guild_id = str(interaction.guild.id)
        guild_config = self.get_music_config(guild_id)
        if interaction.guild.voice_client and interaction.guild.voice_client.is_paused():
            interaction.guild.voice_client.resume()
            await interaction.response.send_message("音樂已恢復播放。", silent=True)
        else:
            await interaction.response.send_message("音樂目前不是暫停狀態。", silent=True)
        await delete_after_delay(interaction, guild_config['delete_after'])

    @app_commands.command(name="stop", description="停止播放所有音樂，並清空佇列")
    async def stop(self, interaction: discord.Interaction):
        """停止播放所有音樂，並清空佇列"""
        guild_id = str(interaction.guild.id)
        guild_config = self.get_music_config(guild_id)
        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            guild_id = str(interaction.guild.id)
            self.queue_dict[guild_id] = []
            if self.get_current_song_info(guild_id):
                del self.current_song_info[guild_id]
            interaction.guild.voice_client.stop()
            await interaction.response.send_message("音樂已停止播放。", silent=True)
        else:
            await interaction.response.send_message("目前沒有音樂播放。", silent=True)
        await delete_after_delay(interaction, guild_config['delete_after'])

    async def playlist_autocomplete(self, interaction: discord.Interaction, current: str):
        """根據指定的用戶或默認指令輸入者動態列出歌單名稱(@app_commands.autocomplete(playlist_name=playlist_autocomplete))"""
        user = interaction.namespace.user or interaction.user  # 如果未指定用戶，默認為指令發起者
        playlists = self.load_playlists()
        user_id = str(user.id)
        user_playlists = playlists.get(user_id, {})  # 獲取指定用戶的歌單
        
        # 根據當前輸入的文本過濾歌單名稱
        return [
            app_commands.Choice(name=playlist_name, value=playlist_name)
            for playlist_name in user_playlists.keys()
            if current.lower() in playlist_name.lower()
        ][:25]  # Discord 限制最多提供 25 個選項
        
    @app_commands.command(name="playlist_add", description="將歌曲添加到用戶歌單")
    @app_commands.describe(playlist_name="歌單名稱(輸入不存在歌單時，將會自動建立新歌單)", url="'一首'歌曲的網址")
    @app_commands.autocomplete(playlist_name=playlist_autocomplete)
    async def playlist_add(self, interaction: discord.Interaction, playlist_name: str, url: str):
        """將歌曲添加到用戶歌單"""
        guild_id = str(interaction.guild.id)
        guild_config = self.get_music_config(guild_id)
        await interaction.response.defer(ephemeral=True)
        playlists = self.load_playlists()
        user_id = str(interaction.user.id)
        
        if user_id not in playlists:
            playlists[user_id] = {}

        if playlist_name not in playlists[user_id]:
            playlists[user_id][playlist_name] = []

        video_id = extract_video_id(url)
        loop = asyncio.get_running_loop()
        # 使用 ProcessPoolExecutor 來執行多進程操作，來降低IO對主進程影響
        with concurrent.futures.ProcessPoolExecutor() as executor:
            future = loop.run_in_executor(executor, fetch_detailed_music_info, video_id)
            info = await future
            
        # 錯誤訊息以str形式回傳，以防型態不可分割問題
        if type(info) is str:
            await interaction.followup.send(f"無法從 YouTube 匯入歌曲：{info}", ephemeral=True, silent=True)
            await delete_after_delay(interaction, guild_config['delete_after'])
            return
        
        formatted_info = f"{info['id']}+{info['title']}"
        # 檢查歌單是否已經存在這首歌
        if formatted_info not in playlists[user_id][playlist_name]:
            playlists[user_id][playlist_name].append(formatted_info)
            self.save_playlists(playlists)
            await interaction.followup.send(f"歌曲`{info['title']}`已加入到歌單 `{playlist_name}`。", ephemeral=True, silent=True)
        else:
            await interaction.followup.send(f"歌曲`{info['title']}`已存在於歌單 `{playlist_name}`。", ephemeral=True, silent=True)
        await delete_after_delay(interaction, guild_config['delete_after'])
            
    @app_commands.command(name="playlist_remove", description="從用戶歌單中移除歌曲，使用索引")
    @app_commands.describe(playlist_name="歌單名稱", index="欲移除歌曲在歌單中的索引(第x首)")
    @app_commands.autocomplete(playlist_name=playlist_autocomplete)
    async def playlist_remove(self, interaction: discord.Interaction, playlist_name: str, index: int):
        """從用戶歌單中移除歌曲，使用索引"""
        guild_id = str(interaction.guild.id)
        guild_config = self.get_music_config(guild_id)
        playlists = self.load_playlists()
        user_id = str(interaction.user.id)
        
        # 檢查歌單是否存在
        if user_id not in playlists or playlist_name not in playlists[user_id]:
            await interaction.response.send_message(f"歌單 `{playlist_name}` 不存在。", ephemeral=True, silent=True)
            await delete_after_delay(interaction, guild_config['delete_after'])
            return

        songs = playlists[user_id][playlist_name]

        if 1 <= index <= len(songs):
            removed_song = songs.pop(index - 1)  # 使用索引移除歌曲
            if not playlists[user_id][playlist_name]:
                del playlists[user_id][playlist_name]
            if not playlists[user_id]:
                del playlists[user_id]
            self.save_playlists(playlists)
            await interaction.response.send_message(f"已從歌單 `{playlist_name}` 移除：{removed_song.split('+', 1)[1]}", ephemeral=True, silent=True)
        else:
            await interaction.response.send_message(f"索引 `{index}` 無效。", ephemeral=True, silent=True)
        await delete_after_delay(interaction, guild_config['delete_after'])
    
    def clear_playlist(self, user_id, playlist_name):
        """移除指定用戶的歌單(playlist_clear)"""
        playlists = self.load_playlists()
        
        # 確保用戶存在
        if str(user_id) in playlists:
            if playlist_name in playlists[str(user_id)]:
                # 刪除歌單
                del playlists[str(user_id)][playlist_name]
                
                # 如果用戶的歌單列表變空，刪除用戶條目
                if not playlists[str(user_id)]:
                    del playlists[str(user_id)]
            
                # 保存更新後的歌單
                self.save_playlists(playlists)
                return True
        
        return False
    
    @app_commands.command(name="playlist_clear", description="清除用戶的指定歌單。")
    @app_commands.autocomplete(playlist_name=playlist_autocomplete)
    async def playlist_clear(self, interaction: discord.Interaction, playlist_name: str):
        """清除用戶的指定歌單。"""
        guild_id = str(interaction.guild.id)
        guild_config = self.get_music_config(guild_id)
        user_id = str(interaction.user.id)
        
        # 調用刪除歌單函數
        if self.clear_playlist(user_id, playlist_name):
            await interaction.response.send_message(f"歌單 `{playlist_name}` 已成功清除。", ephemeral=True, silent=True)
        else:
            await interaction.response.send_message(f"未能找到或清除歌單 `{playlist_name}`。", ephemeral=True, silent=True)
        await delete_after_delay(interaction, guild_config['delete_after'])
        
    @app_commands.command(name="playlist_show", description="展示用戶的歌單")
    @app_commands.describe(user="用戶", playlist_name="歌單名稱")
    @app_commands.autocomplete(playlist_name=playlist_autocomplete)
    async def playlist_show(self, interaction: discord.Interaction, user: discord.User = None, playlist_name: str = None):
        """展示用戶的歌單"""
        guild_id = str(interaction.guild.id)
        guild_config = self.get_music_config(guild_id)
        # 預設用戶為自己
        if user is None:
            user = interaction.user

        playlists = self.load_playlists()
        user_id = str(user.id)

        # 檢查歌酖是否存在
        if user_id not in playlists or (playlist_name and playlist_name not in playlists[user_id]):
            await interaction.response.send_message(f"該用戶 `{user}` 沒有歌單 `{playlist_name}`。", silent=True)
            await delete_after_delay(interaction, guild_config['delete_after'])
            return
        
        chunk_size = 10  # 每個嵌入中顯示的最大歌曲數量
        
        if playlist_name:
            songs = playlists[user_id].get(playlist_name, [])
            if songs:
                embeds = []  # 用來存儲所有嵌入的列表

                # 分段顯示歌曲
                for i in range(0, len(songs), chunk_size):
                    embed = discord.Embed(
                        title=f"🎵 {user.display_name} 的歌單 - {playlist_name} (第 {i // chunk_size + 1} 頁 / 共 {(len(songs) + chunk_size - 1) // chunk_size} 頁)",
                        description=f"🎶 以下是用戶 `{user}` 的歌單 `{playlist_name}` 的內容 (共 `{len(songs)}` 首音樂)：",
                        color=discord.Color.green()
                    )
                    embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)

                    # 添加這批次的歌曲到嵌入
                    song_list = [f"{j + 1}. [{truncate_song_title(song.split('+', 1)[1])}](https://youtu.be/{song.split('+', 1)[0]})" for j, song in enumerate(songs[i:i + chunk_size], start=i)]
                    playlist_content = "\n".join(song_list)
                    embed.add_field(name="歌曲列表", value=playlist_content, inline=False)

                    embeds.append(embed)

                # 發送嵌入
                view = PageView(embeds, interaction.user, guild_config['delete_after'])
                await interaction.response.send_message(embed=embeds[0], view=view, silent=True)
            else:
                await interaction.response.send_message(f"用戶 `{user}` 的歌單 `{playlist_name}` 是空的。", silent=True)
        else:
            all_playlists = playlists.get(user_id, {})
            if all_playlists:
                embeds = []  # 用來存儲所有嵌入的列表
                playlist_entries = [f"**- {name}** *共 `{len(songs)}` 首音樂*" for i, (name, songs) in enumerate(all_playlists.items())]

                # 分段顯示歌單名稱與歌曲數量
                for i in range(0, len(playlist_entries), chunk_size):
                    embed = discord.Embed(
                        title=f"🎵 {user.display_name} 的所有歌單 (第 {i // chunk_size + 1} 頁 / 共 {(len(playlist_entries) + chunk_size - 1) // chunk_size} 頁)",
                        description=f"🎶 以下是用戶 `{user}`的所有歌單與歌曲數量 (共 `{len(playlist_entries)}` 個歌單)：",
                        color=discord.Color.blue()
                    )
                    embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
                    
                    # 將部分歌單內容加入嵌入
                    playlist_content = "\n".join(playlist_entries[i:i + chunk_size])
                    embed.add_field(name="歌單列表", value=playlist_content, inline=False)
                    
                    embeds.append(embed)

                # 發送嵌入
                view = PageView(embeds, interaction.user, guild_config['delete_after'])
                await interaction.response.send_message(embed=embeds[0], view=view, silent=True)
            else:
                await interaction.response.send_message(f"用戶 `{user}` 沒有任何歌單。", silent=True)
        await delete_after_delay(interaction, guild_config['delete_after'])
                
    @app_commands.command(name="playlist_play", description="播放用戶的歌單")
    @app_commands.describe(playlist_name="歌單名稱", user="用戶")
    @app_commands.autocomplete(playlist_name=playlist_autocomplete)
    async def playlist_play(self, interaction: discord.Interaction, user: discord.User = None, playlist_name: str = None):
        """播放用戶的歌單"""
        guild_id = str(interaction.guild.id)
        guild_config = self.get_music_config(guild_id)
        playlists = self.load_playlists()
        # 預設用戶為自己
        if user is None:
            user = interaction.user
            
        user_id = str(user.id)
        
        # 檢查是否指定了 playlist_name
        if playlist_name:
            if playlist_name not in playlists[user_id]:
                await interaction.response.send_message(f"用戶 `{user}` 的歌單 `{playlist_name}` 不存在。", ephemeral=True)
                await delete_after_delay(interaction, guild_config['delete_after'])
                return

            song_urls = playlists[user_id][playlist_name]
            if not song_urls:
                await interaction.response.send_message(f"用戶 `{user}` 的歌單 `{playlist_name}` 是空的。", ephemeral=True)
                await delete_after_delay(interaction, guild_config['delete_after'])
                return
        else:
            # 如果沒有指定 playlist_name，則將所有歌單中的歌曲加入佇列
            playlist_name = "全部歌單"
            song_urls = []
            try:
                for pl_name, urls in playlists[user_id].items():
                    song_urls.extend(urls)
            except KeyError:
                pass
            
            if not song_urls:
                await interaction.response.send_message(f"用戶 `{user}` 的所有歌單都沒有歌曲。", ephemeral=True)
                await delete_after_delay(interaction, guild_config['delete_after'])
                return
        
        # 檢查使用者是否在語音頻道
        if interaction.user.voice is None:
            await interaction.response.send_message("請先加入一個語音頻道！", ephemeral=True, silent=True)
            await delete_after_delay(interaction, guild_config['delete_after'])
            return

        # 取得語音頻道並連接
        voice_channel = interaction.user.voice.channel
        if interaction.guild.voice_client is None:
            await voice_channel.connect()
        elif interaction.guild.voice_client.channel != voice_channel:
            await interaction.guild.voice_client.move_to(voice_channel)

        await interaction.response.defer()
        # 隨機打亂歌單順序
        random.shuffle(song_urls)
        # 添加歌單中的所有歌曲到佇列
        for url in song_urls:
            self.append_queue_dict(guild_id, url)
        
        await interaction.followup.send(f"用戶 `{user}` 的歌單 `{playlist_name}` 中的歌曲已加入佇列並開始播放。當前佇列長度：{self.get_queue_len(guild_id)}", silent=True)
        # 播放佇列中的音樂
        if not self.get_current_song_info(guild_id):
            await self.play_next(interaction)
        
        await delete_after_delay(interaction, guild_config['delete_after'])
            
    @app_commands.command(name="playlist_import", description="從YouTube播放清單匯入所有(或是[legnth]首)歌曲至指定歌單")
    @app_commands.describe(playlist_url="欲匯入的播放清單網址", playlist_name="歌單名稱(輸入不存在歌單時，將會自動建立新歌單)", length="匯入x首歌(範圍1~200)")
    @app_commands.autocomplete(playlist_name=playlist_autocomplete)
    async def playlist_import(self, interaction: discord.Interaction, playlist_url: str, playlist_name: str, length: int = None):
        """從YouTube播放清單匯入所有(或是[legnth]首)歌曲至指定歌單"""
        guild_id = str(interaction.guild.id)
        guild_config = self.get_music_config(guild_id)
        if length != None and (length < 1 or length > 200):
            await interaction.response.send_message(f"[length] 的範圍僅限於1~200", ephemeral=True, silent=True)
            await delete_after_delay(interaction, guild_config['delete_after'])
            return
        
        ydl_opts = {
            'extract_flat': 'in_playlist',  # 僅提取播放清單中的影片資訊
            'quiet': True,
        }
        
        await interaction.response.defer()
        # 使用 ProcessPoolExecutor 來執行多進程操作，來降低IO對主進程影響
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as executor:
            future = loop.run_in_executor(executor, youtube_dl_process, playlist_url, ydl_opts, length)
            formatted_infos = await future
        
        # 錯誤訊息以str形式回傳，以防型態不可分割問題
        if type(formatted_infos) is str:
            await interaction.followup.send(f"無法從 YouTube 播放清單匯入歌曲：{formatted_infos}", silent=True)
            await delete_after_delay(interaction, guild_config['delete_after'])
            return
        
        # 將所有影片添加到指定的歌單
        playlists = self.load_playlists()
        user_id = str(interaction.user.id)

        # 自動為用戶建立新歌單
        if user_id not in playlists:
            playlists[user_id] = {}
        if playlist_name not in playlists[user_id]:
            playlists[user_id][playlist_name] = []

        # 檢查每首歌曲是否已存在於歌單中
        added_count = 0
        for info in formatted_infos:
            if info not in playlists[user_id][playlist_name]:
                playlists[user_id][playlist_name].append(info)
                added_count += 1
        
        self.save_playlists(playlists)
        await interaction.followup.send(f"已將 {added_count} 首新歌加入到歌單 `{playlist_name}`。", silent=True)
        await delete_after_delay(interaction, guild_config['delete_after'])


    @app_commands.command(name="playlist_random", description="將所有已存在的音樂檔案隨機加入播放佇列")
    async def playlist_random(self, interaction: discord.Interaction):
        """將所有已存在的音樂檔案隨機加入播放佇列"""
        guild_id = str(interaction.guild.id)
        guild_config = self.get_music_config(guild_id)
        # 檢查使用者是否在語音頻道
        if interaction.user.voice is None:
            await interaction.response.send_message("請先加入一個語音頻道！", ephemeral=True, silent=True)
            await delete_after_delay(interaction, guild_config['delete_after'])
            return

        # 取得語音頻道並連接
        voice_channel = interaction.user.voice.channel
        if interaction.guild.voice_client is None:
            await voice_channel.connect()
        elif interaction.guild.voice_client.channel != voice_channel:
            await interaction.guild.voice_client.move_to(voice_channel)
            
        # 設定下載目錄路徑
        download_dir = 'download'
        
        # 取得所有下載的文件列表
        music_files = [f for f in os.listdir(download_dir) if f.endswith(".mp3")]

        if not music_files:
            await interaction.response.send_message("沒有找到任何已下載的音樂文件。", silent=True)
            await delete_after_delay(interaction, guild_config['delete_after'])
            return

        # 將文件隨機打亂
        random.shuffle(music_files)
        # 將隨機順序的文件加入播放佇列
        for file in music_files:
            formatted_info = file.rsplit(".", 1)[0]  # 文件名格式為 "id+title.mp3"
            self.queue_dict[guild_id].append(formatted_info)

        await interaction.response.send_message(f"已將 {len(music_files)} 首音樂隨機加入播放佇列。", silent=True)
        # 如果沒有正在播放的歌曲，開始播放
        if not self.get_current_song_info(guild_id):
            await self.play_next(interaction)
        await delete_after_delay(interaction, guild_config['delete_after'])
    
    @app_commands.command(name="help_music", description="展示音樂機器人指令說明")
    async def help_music(self, interaction: discord.Interaction):
        """展示音樂機器人指令說明"""
        
        def add_command_field(embed: discord.Embed, name: str, value: str):
            """輔助函式來簡化添加指令字段到 Embed"""
            embed.add_field(
                name=name,
                value=value,
                inline=False if len(name)>20 else True
            )
            
        embed = discord.Embed(
            title="🎵 音樂機器人指令",
            description="🎶 以下是音樂機器人的所有指令。",
            color=0xE800E8
        )
        
        embed.set_author(name=self.bot.user.display_name, icon_url=self.bot.user.avatar.url)
        embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)
        
        add_command_field(embed, "/help_music", "展示這個指令說明。")
        add_command_field(embed, "/set_config [music_volume] [delete_after]", "設定音樂機器人的配置。")
        add_command_field(embed, "/join", "將機器人加到你現在的頻道。")
        add_command_field(embed, "/leave", "使機器人離開當前頻道。")
        add_command_field(embed, "/play [url]", "播放音樂或將音樂加入佇列。")
        add_command_field(embed, "/current", "顯示當前播放的音樂。")
        add_command_field(embed, "/queue_show", "顯示當前佇列中的所有音樂。")
        add_command_field(embed, "/queue_shuffle", "打亂目前佇列中的音樂順序。")
        add_command_field(embed, "/skip", "跳過當前歌曲，播放佇列中的下一首歌曲。")
        add_command_field(embed, "/pause", "暫停音樂。")
        add_command_field(embed, "/resume", "恢復播放音樂。")
        add_command_field(embed, "/stop", "停止播放所有音樂，並清空佇列。")
        add_command_field(embed, "/playlist_add [playlist_name] [url]", "將歌曲添加到用戶歌單。")
        add_command_field(embed, "/playlist_remove [playlist_name] [index]", "從用戶歌單中移除歌曲。")
        add_command_field(embed, "/playlist_clear [playlist_name]", "清除用戶的指定歌單。")
        add_command_field(embed, "/playlist_show [user] [playlist_name]", "展示用戶的歌單。")
        add_command_field(embed, "/playlist_play [user] [playlist_name]", "播放用戶的歌單(隨機順序)。")
        add_command_field(embed, "/playlist_import [playlist_url] [playlist_name] [length]", "從YouTube播放清單匯入所有(或是[length]首)歌曲至指定歌單。")
        add_command_field(embed, "/playlist_random", "將所有已存在的音樂檔案隨機加入播放佇列。")
        
        embed.set_footer(text="如果沒辦法用，就是機器人不在線")
        await interaction.response.send_message(embed=embed, silent=True)

async def setup(bot):
    await bot.add_cog(Music(bot))