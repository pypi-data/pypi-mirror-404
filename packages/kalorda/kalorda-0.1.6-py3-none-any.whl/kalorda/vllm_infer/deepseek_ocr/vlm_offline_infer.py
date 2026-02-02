from typing import Optional, Tuple

import vllm

# 根据vllm版本选择不同的实现类
if vllm.__version__ >= "0.11.2":
    from .vlm_offline_infer_v11_2 import DeepseekOCRInfer as _DeepseekOCRInferV11_2
if vllm.__version__ < "0.11.2":
    from .vlm_offline_infer_v10_1 import DeepseekOCRInfer as _DeepseekOCRInferV10_1


class DeepseekOCRInfer:
    """统一的Deepseek OCR推理接口，根据vllm版本自动选择合适的实现"""

    def __init__(self, model_weights_dir: str, lora_weights_dir: str = None):
        """初始化OCR推理器

        Args:
            model_weights_dir: 模型权重目录路径
        """
        # 根据vllm版本选择不同的实现类
        # 注：vllm暂时不支持deepseek_ocr挂载lora适配器进行推理
        lora_weights_dir = None

        if vllm.__version__ >= "0.11.2":
            self._impl = _DeepseekOCRInferV11_2(model_weights_dir, lora_weights_dir)
        else:
            self._impl = _DeepseekOCRInferV10_1(model_weights_dir, lora_weights_dir)

    def generate(self, image_file: str) -> Optional[Tuple[str, int]]:
        """对图片进行OCR推理

        Args:
            image_file: 图片文件路径

        Returns:
            包含OCR结果和token数量的元组，如果失败返回None
        """
        return self._impl.generate(image_file)
