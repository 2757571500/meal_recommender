import requests


def send_push(push_url, title, content):
    """通过 ShowDoc 推送消息到微信。

    API 文档: https://push.showdoc.com.cn/server/api/push/{token}
    请求方式: POST，表单格式
    参数:
        title: 消息标题
        content: 消息内容。支持文本、markdown 和 html
    push_url 为空时跳过推送。
    """
    if not push_url:
        print("推送地址未配置，跳过推送")
        return

    try:
        data = {"title": title, "content": content}
        resp = requests.post(push_url, data=data, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        if result.get("error_code") == 0:
            print("推送成功")
        else:
            print(f"推送失败: {result.get('error_message', '未知错误')}")
    except Exception as e:
        print(f"推送异常: {e}")
