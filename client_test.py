import argparse
import base64
import json
import requests
from pathlib import Path


def send_image_to_server(image_path: str, server_url: str = "http://localhost:8000"):
    """
    将本地图片发送到服务器进行处理
    
    Args:
        image_path: 本地图片路径
        server_url: 服务器地址，默认为 http://localhost:8000
    """
    # 检查文件是否存在
    if not Path(image_path).exists():
        print(f"错误: 文件 {image_path} 不存在")
        return

    # 读取图片文件并转换为base64
    with open(image_path, "rb") as image_file:
        image_binary = image_file.read()
        image_base64 = base64.b64encode(image_binary).decode('utf-8')

    # 添加data URI前缀 (可选，取决于服务器期望的格式)
    image_base64_with_prefix = f"data:image/jpeg;base64,{image_base64}"

    # 准备请求数据
    payload = {
        "image_base64": image_base64_with_prefix
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        # 发送POST请求到服务器
        response = requests.post(f"{server_url}/predict", 
                                data=json.dumps(payload), 
                                headers=headers)
        
        # 检查响应状态
        if response.status_code == 200:
            print("请求成功!")
            print("响应内容:")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print(f"请求失败，状态码: {response.status_code}")
            print("错误信息:", response.text)
            
    except requests.exceptions.ConnectionError:
        print(f"连接错误: 无法连接到服务器 {server_url}")
        print("请确保服务器正在运行且地址正确")
    except requests.exceptions.RequestException as e:
        print(f"请求发生错误: {e}")


def main():
    parser = argparse.ArgumentParser(description="向图像处理服务器发送图片进行测试")
    parser.add_argument("image_path", help="要发送的图片文件路径")
    parser.add_argument("--server-url", "-u", default="http://localhost:8000",
                        help="服务器地址 (默认: http://localhost:8000)")
    
    args = parser.parse_args()
    
    send_image_to_server(args.image_path, args.server_url)


if __name__ == "__main__":
    main()