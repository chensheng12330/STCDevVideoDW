
# python3 功能有待完善,
# https://x.com/cs_sherwin2018/status/1868981034626462185

import yt_dlp

# 设置视频 URL
video_url = 'https://x.com/StarLuxeUS/status/1868981034626462185'

# 配置下载选项
ydl_opts = {
    'format': 'best',  #'worst'
    'outtmpl': 'downloaded_video1.%(ext)s', 
    'username': 'xxxxx',  # 替换为你的 X 账号用户名
    'password': '5xxxx4@twitteR', # 替换为你的 X 账号密码
}

# 下载视频
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([video_url])
