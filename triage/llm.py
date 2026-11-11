import os
import threading
from dataclasses import dataclass, field

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, ValidationError

load_dotenv()

DEFAULT_MODEL = "baidu/ernie-5.5-flash-preview:free"


class LLMError(Exception):
    pass


@dataclass
class Usage:
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def add(self, usage):
        # в workflow два запроса идут параллельно
        with self.lock:
            self.calls += 1
            if usage is not None:
                self.prompt_tokens += usage.prompt_tokens or 0
                self.completion_tokens += usage.completion_tokens or 0

    @property
    def total_tokens(self):
        return self.prompt_tokens + self.completion_tokens


def extract_json(text):
    # иногда модель пишет ```json ... ``` или текст вокруг
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        return text[start:end + 1]
    return text


class LLMClient:
    def __init__(self, model=None):
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise LLMError("Нет OPENROUTER_API_KEY, создайте .env по образцу .env.example")
        self.model = model or os.getenv("LLM_MODEL") or DEFAULT_MODEL
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            timeout=60,
            max_retries=5,
        )

    def ask_json(self, system, user, schema, usage):
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        error = ""
        for _ in range(2):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0,
                    max_tokens=4000,
                    response_format={"type": "json_object"},
                )
            except Exception as e:
                raise LLMError(f"ошибка API: {e}") from e

            usage.add(response.usage)
            if not response.choices:
                raise LLMError(f"пустой ответ API: {getattr(response, 'error', None)}")
            text = response.choices[0].message.content or ""
            try:
                return schema.model_validate_json(extract_json(text))
            except ValidationError as e:
                error = str(e)
                messages.append({"role": "assistant", "content": text})
                messages.append({"role": "user", "content": f"Ответ не прошел проверку:\n{error}\nИсправь JSON."})
        raise LLMError(f"модель два раза вернула неправильный ответ: {error[:300]}")
