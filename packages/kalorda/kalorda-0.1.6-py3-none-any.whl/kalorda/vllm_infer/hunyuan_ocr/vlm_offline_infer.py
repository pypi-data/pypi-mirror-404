from PIL import Image
from vllm import LLM, SamplingParams
from vllm.lora.request import LoRARequest

from kalorda.utils.logger import logger

from .prompts import hunyuan_prompt


class HunyuanOCRInfer:
    max_tokens = 20480
    max_model_len = 20480
    max_num_batched_tokens = 20480
    gpu_memory_utilization = 0.8

    def __init__(self, model_weights_dir: str, lora_weights_dir: str = None):
        self.engine = LLM(
            model=model_weights_dir,
            trust_remote_code=True,
            gpu_memory_utilization=self.gpu_memory_utilization,
            max_model_len=self.max_model_len,
            max_num_batched_tokens=self.max_num_batched_tokens,
            limit_mm_per_prompt={"image": 1},
            enable_lora=lora_weights_dir is not None,
        )

        self.sampling_params = SamplingParams(
            temperature=0.0,
            top_p=0.95,
            seed=1234,
            max_tokens=self.max_tokens,
        )

        placeholder = (
            "<｜hy_place▁holder▁no▁100｜><｜hy_place▁holder▁no▁102｜><｜hy_place▁holder▁no▁101｜>"  # noqa: E501
        )
        self.prompt = f"<｜hy_begin▁of▁sentence｜>{placeholder}{hunyuan_prompt['Document_Parsing']}<｜hy_User｜>"
        self.lora_request = (
            LoRARequest("hunyuan_ocr", 1, lora_local_path=lora_weights_dir) if lora_weights_dir is not None else None
        )

    def generate(self, image_file: str):
        image = Image.open(image_file).convert("RGB")
        inputs = [
            {
                "prompt": self.prompt,
                "multi_modal_data": {"image": [image]},
            }
        ]
        response = self.engine.generate(inputs, self.sampling_params, lora_request=self.lora_request)
        ocr_result = response[0].outputs[0].text
        tokens_count = len(response[0].outputs[0].token_ids)
        return ocr_result, tokens_count
