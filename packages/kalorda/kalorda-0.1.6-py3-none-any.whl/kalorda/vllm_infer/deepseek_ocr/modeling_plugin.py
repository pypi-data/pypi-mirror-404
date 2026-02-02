def register():
    from vllm import ModelRegistry

    if "DeepseekOCRForCausalLM" not in ModelRegistry.get_supported_archs():
        from .deepseek_ocr import DeepseekOCRForCausalLM

        ModelRegistry.register_model("DeepseekOCRForCausalLM", DeepseekOCRForCausalLM)
