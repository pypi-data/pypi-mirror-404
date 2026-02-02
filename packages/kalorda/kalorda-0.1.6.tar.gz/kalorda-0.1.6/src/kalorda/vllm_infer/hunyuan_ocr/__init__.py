import vllm

# hunyuan只支持0.12.0及以上版本的vllm
if vllm.__version__ < "0.12.0":
    pass
