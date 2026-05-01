import requests


class AIClient:
    """OpenAI Chat Completions 兼容接口的封装。

    支持 LongCat、DeepSeek、OpenAI 等任意兼容该格式的 API。
    切换模型只需改 config.json 中的 base_url / api_key / model。
    """

    def __init__(self, base_url, api_key, model, timeout=30):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def chat(self, messages, temperature=0.7, max_tokens=1024):
        """调用大语言模型，返回回复文本。

        messages 格式: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
        异常时向上抛出，由调用方处理。
        """
        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
