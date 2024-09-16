# Discord 音樂機器人

## 主要功能
-   從 YouTube 連結播放音樂
-   創建、添加和移除用戶歌單
-   從 YouTube 播放清單或合輯匯入歌曲
-   隨機播放所有已存在的音樂檔案
-   管理播放佇列： 查看、打亂、跳過、暫停與恢復播放

**⚠️請注意，所有音樂將會先被下載到機器人架設端，然後再播放⚠️**

## 安裝與建置環境
### 1. 使用pip安裝套件：
```
pip install python-dotenv
pip install discord.py
pip install yt-dlp
```
### 2. 安裝 `ffmpeg` 並加入環境變數：
**請自行google並用自己喜歡的方式安裝 `ffmpeg`**
### 3. 創建 `.env` 並文件並添加以下內容：
**在 [Discord Developer Portal](https://discord.com/developers/applications) 創建自己的機器人，然後在資料夾建立 `.env` 檔案並將自己的機器人TOKEN放入**
```
TOKEN="你的discord機器人token"
```
### 4. 運行機器人：
**使用以下指令運行機器人**
```
python bot.py
```
### 5. 開始使用：
**在 Discord 內使用 /help_music 來獲取指令相關說明並開始使用**

## 其他小功能
-   發起活動邀請訊息 `/create_event`
-   對其他人發起猜拳挑戰 `/rps`