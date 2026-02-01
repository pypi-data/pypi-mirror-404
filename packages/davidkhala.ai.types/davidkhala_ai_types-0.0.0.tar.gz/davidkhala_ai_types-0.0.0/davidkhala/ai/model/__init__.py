from typing import Protocol, TypedDict, Any


class MessageDict(TypedDict):
    content: str | list | None
    role: str


class ClientProtocol(Protocol):
    api_key: str
    base_url: str
    model: str | None


class ChatAware:
    def __init__(self):
        self.model = None
        self.messages: list[Any | MessageDict] = []
        self.n = 1

    def as_chat(self, model: str, sys_prompt: str = None):
        self.model = model
        if sys_prompt is not None:
            self.messages = [MessageDict(role='system', content=sys_prompt)]

    def chat(self, *user_prompt, **kwargs): ...

    def messages_from(self, *user_prompt) -> list[MessageDict]:
        from davidkhala.ai.model.chat import messages_from
        messages = list(self.messages)
        messages.extend(messages_from(*user_prompt))
        return messages


class EmbeddingAware:
    def as_embeddings(self, model: str):
        self.model = model

    def encode(self, *_input: str) -> list[list[float]]:
        ...


class AbstractClient(ChatAware, EmbeddingAware, ClientProtocol):

    def connect(self) -> bool:
        ...

    def close(self):
        ...

    def __enter__(self):
        assert self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
