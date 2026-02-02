from fastapi import APIRouter, Depends

from kalorda.constant import OcrModel, TestOCRStatus

# 导入数据库和模型
from kalorda.database.database import (
    DatasetDB,
    DatasetImageDB,
    FineTuneTaskDB,
    SystemConfigDB,
    TestOCRResultDB,
    TrainingRunDB,
    db_manager,
)
from kalorda.utils.api_response import error_response, success_response
from kalorda.utils.i18n import _, t

# 设置日志 - 使用全局日志记录器
from kalorda.utils.logger import logger
from kalorda.utils.security import get_current_active_user

# 创建路由
router = APIRouter(
    prefix="/home",
    tags=["首页接口"],
    responses={
        404: {"description": _("未找到")},
        422: {"description": _("请求参数验证失败")},
    },
)


# 获取首页数据
@router.get("/data")
def home_data(current_user: dict = Depends(get_current_active_user)):
    """
    检查基础模型配置是否存在
    """
    try:
        # 确保数据库连接已打开
        db_manager.get_connection()
        # 1、基础模型信息
        base_ocr_models = OcrModel.get_all_models()
        base_model_infos = [
            {
                "code": model["code"],
                "name": model["name"],
                "desc": model["desc"],
                "url": model["url"],
                "available": False,
            }
            for model in base_ocr_models
        ]

        base_model_weight_dir_keys = [f"{model['code']}_weights_dir" for model in base_ocr_models]
        base_model_configs = SystemConfigDB.select().where(SystemConfigDB.config_key.in_(base_model_weight_dir_keys))
        if base_model_configs:
            for model_info in base_model_infos:
                model_weight_dir = base_model_configs.filter(
                    SystemConfigDB.config_key == f"{model_info['code']}_weights_dir"
                ).first()
                if model_weight_dir and model_weight_dir.config_value != "":
                    model_info["available"] = True

        # 2、数据统计
        dataset_count = DatasetDB.select_active().count()
        dataset_image_count = DatasetImageDB.select_active().count()
        fine_tune_task_count = FineTuneTaskDB.select_active().count()
        training_run_count = TrainingRunDB.select_active().count()
        test_ocr_result_count = (
            TestOCRResultDB.select().where(TestOCRResultDB.status == TestOCRStatus.completed["value"]).count()
        )

        data = {
            "base_model_infos": base_model_infos,
            "dataset_count": dataset_count,
            "dataset_image_count": dataset_image_count,
            "fine_tune_task_count": fine_tune_task_count,
            "training_run_count": training_run_count,
            "test_ocr_result_count": test_ocr_result_count,
        }

        return success_response(data)
    except Exception as e:
        logger.error(f"首页数据获取失败: {e}")
        return error_response(_("数据获取失败"))
