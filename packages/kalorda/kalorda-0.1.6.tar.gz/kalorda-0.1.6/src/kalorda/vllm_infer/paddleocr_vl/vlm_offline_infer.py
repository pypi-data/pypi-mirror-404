from PIL import Image
from vllm import LLM, SamplingParams
from vllm.lora.request import LoRARequest

from kalorda.utils.logger import logger


class PaddleOCRVLInfer:
    max_tokens = 16384
    max_model_len = 16384
    max_num_batched_tokens = 16384
    gpu_memory_utilization = 0.8

    def __init__(self, model_weights_dir: str, lora_weights_dir: str = None):
        # 注：vllm暂时不支持paddleocr_vl挂载lora适配器进行推理
        lora_weights_dir = None

        self.engine = LLM(
            model=model_weights_dir,
            trust_remote_code=True,
            gpu_memory_utilization=self.gpu_memory_utilization,
            max_model_len=self.max_model_len,
            max_num_batched_tokens=self.max_num_batched_tokens,
            enable_lora=lora_weights_dir is not None,
        )
        self.sampling_params = SamplingParams(temperature=0, top_p=0.95, max_tokens=self.max_tokens)
        PROMPTS = {
            "ocr": "OCR:",
            "table": "Table Recognition:",
            "formula": "Formula Recognition:",
            "chart": "Chart Recognition:",
        }
        placeholder = "<|IMAGE_START|><|IMAGE_PLACEHOLDER|><|IMAGE_END|>"
        self.prompt = f"<|begin_of_sentence|>User: {PROMPTS['ocr']}{placeholder}\nAssistant: "
        self.lora_request = (
            LoRARequest("paddleocr_vl", 1, lora_local_path=lora_weights_dir) if lora_weights_dir is not None else None
        )

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
