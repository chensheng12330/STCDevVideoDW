# python3  
# Auth by Sherwin.Chen  
# Date: 2024-12-14

import json
import requests
import os
from tqdm import tqdm  # 引入tqdm库用于显示进度条

# 生成URL数组
base_url = "https://www.stcaimcu.com/plugin.php?id=x7ree_v:x7ree_v&code_7ree=1&id_7ree="
urls = []

# 文件名
filename = 'STC32G_Video.json'

# 如果文件已存在，先删除
if os.path.exists(filename):
    os.remove(filename)
    print(f"File {filename} already exists and has been deleted.")

# 创建一个范围，从143到186
url_range = range(143, 187)

# 使用tqdm显示进度条
for i in tqdm(url_range, desc="Processing URLs", unit="URL"):
    url = base_url + str(i)
    
    # 检查URL是否能成功访问
    try:
        response = requests.get(url)
        if response.status_code == 200:  # 请求成功，保存URL
            urls.append({"url": url, "id_7ree": i})
        else:
            print(f"URL {url} returned status code {response.status_code}. Skipping.")
    except requests.RequestException as e:
        # 请求发生错误（如连接失败等），跳过该URL
        print(f"Error accessing {url}: {e}. Skipping.")

# 保存为JSON文件
with open(filename, 'w') as f:
    json.dump(urls, f, indent=4)

print(f"URLs have been saved to {filename}")
