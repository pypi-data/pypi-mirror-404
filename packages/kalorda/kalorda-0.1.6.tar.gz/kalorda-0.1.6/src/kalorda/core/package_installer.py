import os
import shutil
import subprocess
import tempfile
import uuid

from kalorda.utils.logger import logger


# 特定情况下需要安装库的分支版本，但不影响主项目的库版本，如主项目最新的transformers，但微调任务可能需要4.46.3版本
def install_branch_package(package: str, install_path: str = None):
    """
    安装库的分支版本到指定目录
    """

    if not install_path:
        install_path = f"{tempfile.gettempdir()}/{uuid.uuid4()}"  # 随机字符
    pip_command = f"pip install {package} --target {install_path} --ignore-installed"
    if not os.path.exists(install_path):
        os.makedirs(install_path)
        # pip在线安装指定库的指定版本到指定目录位置
        result = subprocess.run(
            pip_command,
            shell=True,
            check=False,
        )
        if result.returncode != 0:
            # 删除未安装成功的目录
            shutil.rmtree(install_path)
            logger.error(f"安装 {package} 失败")
            return False, None
    return True, install_path
