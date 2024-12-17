# python3
import requests
from bs4 import BeautifulSoup
import re
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm  # 使用 rich 渲染 tqdm 进度条
from rich.progress import Progress

# 依赖三方库:  rich , tqdm, BeautifulSoup, requests

# 给定的10个网页URL地址
urls = [
    # 替换为实际的视频网页URL
    'https://www.stcaimcu.com/plugin.php?id=x7ree_v:x7ree_v&code_7ree=1&id_7ree=164',
    # 替换为实际的视频网页URL
    'https://www.stcaimcu.com/plugin.php?id=x7ree_v:x7ree_v&code_7ree=1&id_7ree=165',
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
    # title = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5\s-]', '', title)
    # 去除多余空格
    title = ' '.join(title.split())
    # 保留第一个空格之前的数据
    title = title.split('-')[0]
    return title


def load_json(file_path):
    """从 JSON 文件加载数据"""
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def extract_video_data(url_data, existing_urls, output_file='extracted_video_data.json'):
    """
    提取视频 URL 和标题。
    如果本地已存在 output_file，则直接读取该文件数据。
    """
    # 检查是否已经存在 extracted_video_data.json 文件
    if os.path.exists(output_file):
        print(f"File '{output_file}' already exists. Loading existing data...")
        with open(output_file, 'r', encoding='utf-8') as f:
            video_data = json.load(f)
        return video_data

    # 如果文件不存在，继续进行提取
    video_data = []

    print("[blue]Extracting video data from URLs...[/blue]")
    with tqdm(total=len(url_data), desc="Processing URLs", unit="URL") as pbar:
        for item in url_data:
            url = item.get('url')
            id_7ree = item.get('id_7ree')

            # 跳过已存在的 URL
            if url in existing_urls:
                print(f"Skipping already downloaded URL: {url}")
                pbar.update(1)
                continue

            try:
                # 发送 HTTP 请求获取网页内容
                response = requests.get(url, headers=headers)
                response.raise_for_status()

                # 使用 BeautifulSoup 解析网页内容
                soup = BeautifulSoup(response.text, 'html.parser')

                # 提取视频 URL
                video_url = None
                for video_tag in soup.find_all('video'):
                    # 检查 video 标签的 src 属性
                    src = video_tag.get('src')
                    if src and src.endswith('.mp4'):
                        video_url = src
                        break

                    # 检查 <source> 标签
                    for source_tag in video_tag.find_all('source'):
                        src = source_tag.get('src')
                        if src and src.endswith('.mp4'):
                            video_url = src
                            break

                # 提取视频名称
                title_tag = soup.find('title')
                title = title_tag.get_text() if title_tag else 'Untitled'
                title = clean_title(title)

                # 如果找到视频 URL，加入数据列表
                if video_url:
                    video_data.append({
                        'id_7ree': id_7ree,
                        'title': title,
                        'video_url': video_url
                    })

            except requests.exceptions.RequestException as e:
                print(f"Error fetching {url}: {e}")
                continue

            finally:
                # 更新进度条
                pbar.update(1)

    # 提取完成后，将数据保存到 JSON 文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(video_data, f, ensure_ascii=False, indent=4)

    print(f"[green]Extracted video data saved to '{output_file}'.[/green]")
    return video_data

def save_to_json(data, filename):
    # 获取当前执行脚本所在的文件夹路径
    script_dir = os.path.dirname(os.path.realpath(__file__))
    # 拼接出文件路径
    file_path = os.path.join(script_dir, filename)

    # 将数据保存到JSON文件
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def download_with_rich(video_url, file_path):
    """下载视频文件并显示进度条"""
    response = requests.get(video_url, headers=headers, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get('content-length', 0))
    with open(file_path, "wb") as f, tqdm(
        total=total_size,
        unit="B",
        unit_scale=True,
        desc=f"Downloading {os.path.basename(file_path)}"
    ) as progress:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                progress.update(len(chunk))
    return True


def download_video(video_info, folder="STCVideo"):
    """下载单个视频"""
    if not os.path.exists(folder):
        os.makedirs(folder)

    # 获取文件名，带上 id_7ree 前缀
    id_7ree = video_info['id_7ree']
    file_name = f"{id_7ree}-{video_info['title']}.mp4"
    file_path = os.path.join(folder, file_name)

    # 下载视频
    try:
        print(f"Starting download: {file_name}")
        download_with_rich(video_info['video_url'], file_path)
        print(f"[green]Downloaded: {file_name}[/green]")
        return {
            'id_7ree': id_7ree,
            'title': video_info['title'],
            'video_url': video_info['video_url']
        }
    except Exception as e:
        print(f"[red]Failed to download {file_name}: {e}[/red]")
        return None


def download_videos_concurrently(video_info_list, max_workers=2, folder="STCVideo", save_file="save_list_data.json"):
    """
    并发下载视频，并限制最大并行任务数。
    每下载完成一个视频，就立即更新到 save_file 文件中。
    """
    downloaded_videos = []

    # 加载已有的数据
    if os.path.exists(save_file):
        with open(save_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    else:
        existing_data = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_video = {executor.submit(
            download_video, video_info, folder): video_info for video_info in video_info_list}

        for future in as_completed(future_to_video):
            video_info = future_to_video[future]
            try:
                result = future.result()
                if result:  # 只记录下载成功的视频
                    downloaded_videos.append(result)

                    # 立即更新到 save_file
                    existing_data.append(result)
                    with open(save_file, 'w', encoding='utf-8') as f:
                        json.dump(existing_data, f,
                                  ensure_ascii=False, indent=4)

                    print(f"Updated '{save_file}' with {result['title']}")
            except Exception as e:
                print(f"Error downloading {video_info['title']}: {e}")

    return downloaded_videos


def main():
    # 加载本地 JSON 文件数据
    url_data = load_json('STC32G_Video.json')

    # 加载已存在的 URL 数据
    existing_data = load_json('save_list_data.json')
    existing_urls = {item['video_url'] for item in existing_data}

    # 提取视频数据
    video_info = extract_video_data(url_data, existing_urls)

    # 保存提取的视频信息到 JSON 文件
    save_to_json(video_info, 'extracted_video_data.json')

    # 下载视频，限制并发任务数量为 2
    downloaded_videos = download_videos_concurrently(video_info, max_workers=2)

    # 合并下载成功的视频信息到已存在的数据中
    existing_data.extend(downloaded_videos)

    # 保存最终的下载信息到 save_list_data.json
    save_to_json(existing_data, 'save_list_data.json')

    print("[bold green]All downloads are complete. Updated 'save_list_data.json' with successful downloads.[/bold green]")


if __name__ == '__main__':
    main()
