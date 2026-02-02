# 定义messages格式的sft数据实体类
import json
from typing import List, Optional


class SFTDataBuilder:
    def __init__(self, data_format: str) -> None:
        self.data_format = data_format

    def to_json(self, images: str | List[str], prompt: str, content: str):
        if prompt.startswith("<image>") is False:
            prompt = "<image>" + prompt

        dict = None
        if self.data_format.lower() == "chatml":
            dict = DataChatML(images, prompt, content).to_dict()
        if self.data_format.lower() == "query_response" or self.data_format.lower() == "queryresponse":
            dict = DataQueryResponse(images, prompt, content).to_dict()
        if self.data_format.lower() == "alpaca":
            dict = DataAlpaca(images, prompt, "", content).to_dict()
        if self.data_format.lower() == "sharegpt":
            dict = DataShareGPT(images, prompt, content).to_dict()

        return json.dumps(dict, ensure_ascii=False) if dict else ""


class DataChatML:
    def __init__(
        self,
        images: str | List[str],
        user_content: str,
        assistant_content: str,
        system_content: Optional[str] = None,
    ):
        self.images = []
        if isinstance(images, str):
            self.images.append(images)
        else:
            self.images.extend(images)

        self.messages = []
        if system_content:
            self.messages.append({"role": "system", "content": system_content})
        self.messages.append({"role": "user", "content": user_content})
        self.messages.append({"role": "assistant", "content": assistant_content})

    def to_dict(self):
        return {
            "messages": self.messages,
            "images": self.images,
        }


class DataQueryResponse:
    def __init__(self, images: str | List[str], query: str, response: str):
        self.images = []
        if isinstance(images, str):
            self.images.append(images)
        else:
            self.images.extend(images)

        self.query = query
        self.response = response

    def to_dict(self):
        return {
            "query": self.query,
            "response": self.response,
            "images": self.images,
        }


class DataAlpaca:
    def __init__(
        self,
        images: str | List[str],
        instruction: str,
        input: str,
        output: str,
    ):
        self.images = []
        if isinstance(images, str):
            self.images.append(images)
        else:
            self.images.extend(images)

        self.instruction = instruction
        self.input = input
        self.output = output

    def to_dict(self):
        return {
            "instruction": self.instruction,
            "input": self.input,
            "output": self.output,
            "images": self.images,
        }


class DataShareGPT:
    def __init__(
        self,
        image: str | List[str],
        human_value: str,
        gpt_value: str,
        system_value: Optional[str] = None,
    ):
        self.image = image
        self.conversations = []
        self.system_value = system_value
        self.conversations.append(
            {
                "from": "human",
                "value": human_value,
            }
        )
        self.conversations.append(
            {
                "from": "gpt",
                "value": gpt_value,
            }
        )

    def to_dict(self):
        if self.system_value:
            return {
                "system": self.system_value,
                "conversations": self.conversations,
                "image": self.image,
            }
        else:
            return {
                "conversations": self.conversations,
                "image": self.image,
            }
