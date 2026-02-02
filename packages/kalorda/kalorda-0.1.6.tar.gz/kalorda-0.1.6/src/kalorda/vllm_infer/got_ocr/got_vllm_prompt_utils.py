import base64
import glob
from io import BytesIO
from typing import List, Union

import requests
from natsort import natsorted
from PIL import Image

from .conversation import conv_templates
from .pdf_file_utils import pdf_to_image

DEFAULT_IMAGE_TOKEN = "<image>"
DEFAULT_IMAGE_PATCH_TOKEN = "<imgpad>"

DEFAULT_IM_START_TOKEN = "<img>"
DEFAULT_IM_END_TOKEN = "</img>"

stop_token_id = 151645


def get_stop_token_id():
    return stop_token_id


def __get_prompt_input(image_size: int = 1, type: str = "plain", multi_page: bool = False):
    qs = ""
    if type.lower() == "plain":
        qs += "OCR: "
    else:
        qs += "OCR with format: "

    if multi_page:
        qs = "OCR with format across multi pages: "

    qs = f"{DEFAULT_IM_START_TOKEN}{DEFAULT_IMAGE_PATCH_TOKEN * image_size}{DEFAULT_IM_END_TOKEN}\n{qs}"
    # 配置对话模板
    conv_mode = "mpt"
    conv = conv_templates[conv_mode].copy()
    conv.append_message(conv.roles[0], qs)
    conv.append_message(conv.roles[1], None)
    prompt = conv.get_prompt()
    return prompt


def __load_image(image_file):
    # 获取单个图片的tensor
    if isinstance(image_file, Image.Image):
        image = image_file
    elif isinstance(image_file, bytes):
        # 从bytes加载图像并转换为RGB格式
        image = Image.open(BytesIO(image_file)).convert("RGB")
    elif isinstance(image_file, str):
        # 从文件路径或url加载图像并转换为RGB格式
        if image_file.startswith("http"):
            # 加重试逻辑
            try_count = 0
            while try_count < 3:
                try:
                    response = requests.get(image_file, timeout=5)
                    image = Image.open(BytesIO(response.content)).convert("RGB")
                    break
                except Exception as e:
                    print(f"Error loading image from {image_file}: {e}")
                    try_count += 1
        elif image_file.startswith("data:image/"):
            # base64编码的 data:image/png;base64,
            image_data = base64.b64decode(image_file.split("base64,")[1])
            image_bytes = BytesIO(image_data)
            image = Image.open(image_bytes).convert("RGB")
        else:
            image = Image.open(image_file).convert("RGB")

    return image


def __load_image_list(image_file_list):
    # 获取多个图片的tensors
    image_tensors = []
    for image_file in image_file_list:
        image_tensor = __load_image(image_file)
        image_tensors.append(image_tensor)
    return image_tensors


def get_got_prompts(image_list: Union[str, List[str], List[List[str]]], type: str = None, box: List[List[int]] = None):
    if image_list is None:
        raise ValueError("image_list must be a string or a list of strings")
    result_prompt_inputs = []
    result_prompt_images = []
    multi_page = False

    # 增补支持单个pdf文档
    if isinstance(image_list, str) and image_list.endswith(".pdf"):
        image_list = pdf_to_image(image_list)

    image_ext_names = [".png", ".jpg", ".jpeg", ".webp"]

    if isinstance(image_list, str):
        if (
            image_list.startswith("data:image/")
            or image_list.startswith("http")
            or "." + image_list.split(".")[-1].lower() in image_ext_names
        ):
            # 单个图片
            if box is None:
                # 没有指定区域则整图识别
                image = __load_image(image_list)
                input = __get_prompt_input(image_size=1, type=type, multi_page=multi_page)
                result_prompt_inputs.append(input)
                result_prompt_images.append(image)
            elif isinstance(box[0], int):
                # 只有一个裁剪区域，注：这里暂时没有做任何校验坐标是否合理的逻辑
                orginal_image = Image.open(image_list)
                x1, y1, x2, y2 = box
                image = __load_image(orginal_image.crop((x1, y1, x2, y2)))
                input = __get_prompt_input(image_size=1, type=type, multi_page=multi_page)
                result_prompt_inputs.append(input)
                result_prompt_images.append(image)
            else:
                orginal_image = Image.open(image_list)
                # 有多个裁剪区域，每个区域对应一个prompt，每个prompt对应一张图片，普通多图识别模式
                for box_item in box:
                    x1, y1, x2, y2 = box_item
                    image = __load_image(orginal_image.crop((x1, y1, x2, y2)))
                    input = __get_prompt_input(image_size=1, type=type, multi_page=multi_page)
                    result_prompt_inputs.append(input)
                    result_prompt_images.append(image)
        else:
            # 如果不是文件则默认是本地文件夹路径，扫描文件夹下全部图片，进行普通多图识别
            # 普通多图识别，构造多个pompt，每个prompt对应一张图片
            image_folder = image_list if image_list.endswith("/") else image_list + "/"
            image_list = []
            for image_ext_name in image_ext_names:
                image_list.extend(glob.glob(image_folder + "*" + image_ext_name))
            image_list = natsorted(image_list)
            for sub_image in image_list:
                image = __load_image(sub_image)
                input = __get_prompt_input(image_size=1, type=type, multi_page=multi_page)
                result_prompt_inputs.append(input)
                result_prompt_images.append(image)
    elif isinstance(image_list, list):
        # 如果传过来的是一个列表，可能是一个字符串列表["","","",""]，也可能是一个二维字符串列表[["",""],["",""]]
        # 以第一个元素为判断依据，决定是普通模式的多图识别还是multi-page模式的多图识别
        multi_page = isinstance(image_list[0], list)
        if multi_page is False:
            # 普通多图识别，构造多个pompt，每个prompt对应一张图片
            for sub_image in image_list:
                image = __load_image(sub_image)
                input = __get_prompt_input(image_size=1, type=type, multi_page=multi_page)
                result_prompt_inputs.append(input)
                result_prompt_images.append(image)
        else:
            # multi-page多图识别，构造多个prompt,每个prompt放多张图片进行multi-page模式识别
            # 注：每个prompt的多个图片的数量必须一致的
            max_image_size = 1
            for sub_image_list in image_list:
                max_image_size = max(max_image_size, len(sub_image_list))

            for sub_image_list in image_list:
                sub_images = __load_image_list(sub_image_list)
                input = __get_prompt_input(image_size=len(sub_image_list), type=type, multi_page=multi_page)
                result_prompt_inputs.append(input)
                result_prompt_images.append(sub_images)

    if len(result_prompt_inputs) == 0:
        raise ValueError("no image found, please check your image_file params")

    return result_prompt_inputs, result_prompt_images
