#python3
import requests
from bs4 import BeautifulSoup
import re
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm  # 导入 tqdm 进度条库

# 给定的10个网页URL地址
urls = [
    'https://www.stcaimcu.com/plugin.php?id=x7ree_v:x7ree_v&code_7ree=1&id_7ree=162',  # 替换为实际的视频网页URL
    'https://www.stcaimcu.com/plugin.php?id=x7ree_v:x7ree_v&code_7ree=1&id_7ree=163',  # 替换为实际的视频网页URL
    # ...
]


# 设置User-Agent为Chrome浏览器
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36'
}

def clean_title(title):
    # 去除HTML标签
    title = re.sub(r'<.*?>', '', title)
    # 去除特殊符号（保留字母、数字、中文、空格和 - 符号）
    #title = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5\s-]', '', title)
    # 去除多余空格
    title = ' '.join(title.split())
    # 保留第一个空格之前的数据
    title = title.split('-')[0]
    return title


def extract_video_data(urls):
    video_data = []

    for url in urls:
        try:
            # 发送HTTP请求获取网页内容
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # 检查请求是否成功

            # 使用BeautifulSoup解析网页内容
            #print(response.text)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取视频URL（<video>标签中的src属性）
            video_url = None
            
            #print(soup.find_all('video'))
            for video_tag in soup.find_all('video'):
                print(f"video_tag: {video_tag}")
                src = video_tag.get('src')
                print(f"src: {src}")
                if src and src.endswith('.mp4'):  # 检查是否为.mp4链接
                    video_url = src
                    break
                
                 # 如果没有src属性，检查<source>标签
                for source_tag in video_tag.find_all('source'):
                    src = source_tag.get('src')
                    if src and src.endswith('.mp4'):
                        video_url = src
                        break

            # 提取视频名称（<title>标签内容）并清理
            title_tag = soup.find('title')
            title = title_tag.get_text() if title_tag else 'Untitled'
            print(title)
            
            title = clean_title(title)

            print(title)
            print(video_url)
            # 如果找到了视频URL，加入视频数据数组
            if video_url:
                video_data.append({
                    'title': title,
                    'video_url': video_url
                })

        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            continue

    return video_data

def save_to_json(data, filename='save.json'):
    # 获取当前执行脚本所在的文件夹路径
    script_dir = os.path.dirname(os.path.realpath(__file__))
    # 拼接出文件路径
    file_path = os.path.join(script_dir, filename)
    
    # 将数据保存到JSON文件
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def download_video(video_info, folder="STCVideo"):
    if not os.path.exists(folder):
        os.makedirs(folder)  # 如果没有文件夹，创建它

    # 获取视频URL和文件名
    video_url = video_info['video_url']
    file_name = video_info['title'] + ".mp4"
    file_path = os.path.join(folder, file_name)

    # 下载视频
    try:
        print(f"Downloading: {file_name}")
        response = requests.get(video_url, headers=headers, stream=True)
        response.raise_for_status()  # 如果请求失败，会抛出异常

        # 获取文件总大小
        total_size = int(response.headers.get('content-length', 0))

        # 使用 tqdm 显示进度条
        with open(file_path, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=file_name) as pbar:
                for chunk in response.iter_content(chunk_size=8192):  # 分块写入文件
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))  # 更新进度条

        print(f"Downloaded: {file_name}")
        
        # 返回视频名称和地址，表示下载成功
        return {
            'title': video_info['title'],
            'video_url': video_url
        }
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {file_name}: {e}")
        return None  # 如果下载失败，返回 None

def main():
    # 获取视频数据
    video_info = extract_video_data(urls)
    
    # 保存视频信息到 JSON 文件
    save_to_json(video_info)

    # 用于存储已下载视频名称和地址
    downloaded_videos = []

    # 使用多线程下载视频
    with ThreadPoolExecutor(max_workers=4) as executor:
        # 执行下载并收集结果
        results = executor.map(download_video, video_info)
        for result in results:
            if result:  # 只记录下载成功的视频
                downloaded_videos.append(result)

    # 保存下载成功的视频名称和地址到 save.json
    save_to_json(downloaded_videos, filename='save.json')

    print("All downloads are complete and only successful videos have been saved to 'save.json'.")

if __name__ == '__main__':
    main()