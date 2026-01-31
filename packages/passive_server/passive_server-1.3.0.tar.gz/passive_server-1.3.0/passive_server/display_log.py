# pylint: skip-file
"""向页面 websocket 发送数据."""
import threading

import requests


def post_route(route_name: str, data: dict):
    """向网页发送 post 请求.

    Args:
        route_name: 路由名称.
        data: 数据.
    """
    try:
        requests.post(route_name, json=data)
    except Exception:
        pass

def send_post(route_name: str, data: dict):
    """发送 post 路由请求.

    Args:
        route_name: 路由名称.
        data: 数据.
    """
    url = f"http://127.0.0.1:2025/{route_name}"
    threading.Thread(target=post_route, args=(url, data,), daemon=True).start()
