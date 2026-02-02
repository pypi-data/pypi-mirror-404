def register():
    from vllm import ModelRegistry

    if "DotsOCRForCausalLM" not in ModelRegistry.get_supported_archs():
        from .modeling_dots_ocr_vllm import DotsOCRForCausalLM, patch_vllm_chat_placeholder

        ModelRegistry.register_model("DotsOCRForCausalLM", DotsOCRForCausalLM)
        patch_vllm_chat_placeholder()
