import logging
import os
import re
import subprocess
import sys
from typing import Any, Dict

import torch

logger = logging.getLogger(__name__)


def get_torch_version():
    """获取PyTorch版本"""
    try:
        return torch.__version__
    except Exception as e:
        logger.error(f"获取PyTorch版本失败: {str(e)}")
        return ""


def _get_gpu_info_by_nvidia_smi() -> Dict[str, Any]:
    """使用nvidia-smi获取实时GPU信息"""
    try:
        # 查询GPU信息：名称、总显存、已用显存、空闲显存、GPU利用率、温度
        cmd = [
            "nvidia-smi",
            "--query-gpu=gpu_name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu",
            "--format=csv,noheader,nounits",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode != 0:
            logger.error(f"nvidia-smi执行失败: {result.stderr}")
            return {"available": False, "error": "nvidia-smi执行失败", "gpus": []}

        lines = result.stdout.strip().split("\n")
        gpus = []
        total_memory = 0.0
        total_used = 0.0

        for i, line in enumerate(lines):
            if line.strip():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 6:
                    gpu_name = parts[0]
                    memory_total = float(parts[1]) / 1024  # 转换为GB
                    memory_used = float(parts[2]) / 1024  # 转换为GB
                    memory_free = float(parts[3]) / 1024  # 转换为GB
                    gpu_util = parts[4]
                    temperature = parts[5]

                    total_memory += memory_total
                    total_used += memory_used
                    gpus.append(
                        {
                            "id": str(i),
                            "name": gpu_name,
                            "memory_total": memory_total,
                            "memory_used": memory_used,
                            "memory_free": memory_free,
                            "utilization": f"{gpu_util}%",
                            "temperature": f"{temperature}°C",
                        }
                    )

        return {
            "available": True,
            "gpus": gpus,
            "total_memory": total_memory,
            "used_memory": total_used,
            "free_memory": total_memory - total_used,
        }

    except subprocess.TimeoutExpired:
        logger.error("nvidia-smi查询超时")
        return {"available": False, "error": "nvidia-smi查询超时", "gpus": []}
    except FileNotFoundError:
        logger.error("nvidia-smi命令未找到，可能未安装NVIDIA驱动")
        return {"available": False, "error": "nvidia-smi未找到", "gpus": []}
    except Exception as e:
        logger.error(f"获取GPU信息失败: {str(e)}")
        return {"available": False, "error": str(e), "gpus": []}


def _get_gpu_info_by_torch() -> Dict[str, Any]:
    """使用torch获取GPU信息"""
    try:
        if not torch.cuda.is_available():
            return {
                "available": False,
                "gpus": [],
                "total_memory": 0,
                "used_memory": 0,
                "free_memory": 0,
            }

        gpu_count = torch.cuda.device_count()
        gpus = []
        total_memory = 0
        used_memory = 0

        for i in range(gpu_count):
            gpu_memory = torch.cuda.get_device_properties(i).total_memory / (1024**3)  # GB
            total_memory += gpu_memory

            # 尝试获取当前设备的实际显存使用情况
            try:
                torch.cuda.set_device(i)
                memory_allocated = torch.cuda.memory_allocated(i) / (1024**3)
                memory_reserved = torch.cuda.memory_reserved(i) / (1024**3)
                actual_used = max(memory_allocated, memory_reserved)
            except Exception:
                # 如果无法获取实际使用情况，使用估算
                actual_used = 0

            gpus.append(
                {
                    "id": str(i),
                    "name": torch.cuda.get_device_name(i),
                    "memory_total": gpu_memory,
                    "memory_used": actual_used,
                    "memory_free": gpu_memory - actual_used,
                }
            )

            used_memory += actual_used

        return {
            "available": True,
            "gpus": gpus,
            "total_memory": total_memory,
            "used_memory": used_memory,
            "free_memory": total_memory - used_memory,
            "max_concurrent_tasks": max(1, int((total_memory - used_memory) / 10)),
        }
    except Exception as e:
        logger.error(f"获取GPU信息失败: {str(e)}")
        return {
            "available": False,
            "error": str(e),
            "gpus": [],
            "total_memory": 0,
            "used_memory": 0,
            "free_memory": 0,
        }


# 获取系统GPU信息
def get_gpu_info() -> Dict[str, Any]:
    """获取系统GPU信息"""
    # 首先尝试使用nvidia-smi获取
    real_gpu_info = _get_gpu_info_by_nvidia_smi()
    if real_gpu_info["available"]:
        return real_gpu_info
    else:
        # 如果nvidia-smi不可用则使用torch方法
        torch_gpu_info = _get_gpu_info_by_torch()
        return torch_gpu_info


def _get_cuda_version_by_nvidia_smi():
    """使用nvidia-smi获取CUDA版本"""
    try:
        # 运行nvidia-smi命令并获取输出
        result = subprocess.check_output(["nvidia-smi", "", "--format=csv,noheader,nounits"])
        # 移除输出中的换行符并解码
        cuda_version = result.decode("utf-8").strip()
        return cuda_version
    except subprocess.CalledProcessError:
        return ""
    except Exception as e:
        logger.error(f"获取CUDA版本失败: {str(e)}")
        return ""


def _get_cuda_version_by_torch():
    """使用torch获取CUDA版本"""
    try:
        if torch.cuda.is_available():
            return torch.version.cuda
    except Exception as e:
        logger.error(f"获取CUDA版本失败: {str(e)}")
        pass
    return ""


def get_cuda_version():
    """获取CUDA版本"""
    cuda_version = _get_cuda_version_by_nvidia_smi()
    if cuda_version:
        return cuda_version
    else:
        return _get_cuda_version_by_torch()


def get_virtual_env():
    prefix = sys.prefix
    executable = sys.executable
    env_name = os.path.basename(prefix)
    return {
        "sys_executable": executable,
        "sys_prefix": prefix,
        "env_name": env_name,
    }


def get_vllm_version():
    """获取VLLM版本"""
    try:
        import vllm

        return vllm.__version__
    except ImportError:
        return ""


def get_swift_version():
    """获取Swift版本"""
    try:
        import swift

        return swift.__version__
    except ImportError:
        return ""


def get_transformers_version():
    """获取Transformers版本"""
    try:
        import transformers

        return transformers.__version__
    except ImportError:
        return ""


def get_flash_attn_available():
    """检查FlashAttention是否可用"""
    try:
        import flash_attn
        from flash_attn import flash_attn_func

        # 检查是否有可用的CUDA设备
        if not torch.cuda.is_available():
            logger.warning("CUDA设备不可用，FlashAttention检查失败")
            return False

        return flash_attn.__version__ is not None
    except Exception as e:
        logger.error(f"检查FlashAttention失败: {str(e)}")
        return False


def get_package_versions():
    """获取FlashAttention版本"""
    try:
        cmd = [
            "pip",
            "list",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            logger.error(f"pip list执行失败: {result.stderr}")
            return []
        lines = result.stdout.strip().split("\n")
        lines = lines[2:]  # 去掉表头
        # 提取报名和版本号
        packages = []
        for line in lines:
            line = line.strip()
            if line:
                package_name, version = line.split()[0], line.split()[1]
                packages.append((package_name, version))
        return packages

    except ImportError:
        return []
