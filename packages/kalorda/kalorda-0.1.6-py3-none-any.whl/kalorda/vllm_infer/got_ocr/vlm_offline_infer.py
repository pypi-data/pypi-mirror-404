import os

from PIL import Image
from vllm import LLM, SamplingParams
from vllm.lora.request import LoRARequest

from kalorda.utils.logger import logger
from kalorda.vllm_infer.got_ocr.got_vllm_prompt_utils import __get_prompt_input as get_prompt
from kalorda.vllm_infer.got_ocr.got_vllm_prompt_utils import (
    get_stop_token_id,
)


class GotOCRInfer:
    max_tokens = 2048
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
            # hf_overrides={
            #     "architectures": ["Qwen2GotForCausalLM"],
            # },
            enable_lora=lora_weights_dir is not None,
        )
        self.sampling_params = SamplingParams(
            temperature=0.0,
            top_p=0.9,
            max_tokens=self.max_tokens,
            stop_token_ids=[get_stop_token_id()],
        )
        self.prompt = get_prompt(1, "format", False)
        if lora_weights_dir is not None:
            self.lora_request = LoRARequest("got_ocr_lora", 1, lora_local_path=lora_weights_dir)
        else:
            self.lora_request = None

    def generate(self, image_file: str):
        inputs = [
            {
                "prompt": self.prompt,
                "multi_modal_data": {"image": [Image.open(image_file).convert("RGB")]},
            }
        ]
        response = self.engine.generate(inputs, self.sampling_params, lora_request=self.lora_request)
        ocr_result = response[0].outputs[0].text
        tokens_count = len(response[0].outputs[0].token_ids)
        return ocr_result, tokens_count
