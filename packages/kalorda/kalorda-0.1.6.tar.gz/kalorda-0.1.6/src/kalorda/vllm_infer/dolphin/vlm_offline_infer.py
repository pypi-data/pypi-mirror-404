import os

from PIL import Image
from qwen_vl_utils import process_vision_info
from transformers import AutoProcessor
from vllm import LLM, SamplingParams
from vllm.lora.request import LoRARequest

from kalorda.utils.logger import logger

from .prompts import dolphin_prompt
from .utils import (
    check_bbox_overlap,
    parse_layout_string,
    process_coordinates,
    resize_img,
    save_figure_to_local,
)


#  dolphin v2 模型推理
class DolphinInfer:
    max_tokens = 4096
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
            enable_lora=lora_weights_dir is not None,
        )
        self.sampling_params = SamplingParams(
            temperature=0.0,
            top_p=0.95,
            logprobs=0,
            max_tokens=self.max_tokens,
            prompt_logprobs=None,
            skip_special_tokens=True,
        )

        self.processor = AutoProcessor.from_pretrained(model_weights_dir)
        if lora_weights_dir is not None:
            self.lora_request = LoRARequest("dolphin_lora", 1, lora_local_path=lora_weights_dir)
        else:
            self.lora_request = None

    def generate(self, image_file: str):
        image = Image.open(image_file).convert("RGB")

        image_name = os.path.splitext(os.path.basename(image_file))[0]
        save_dir = image_file.split(image_name)[0]  # 截图保存目录

        # Stage 1: Page-level layout and reading order parsing
        layout_response = self.model_infer([image], [dolphin_prompt["layout"]])
        layout_results = layout_response[0].outputs[0].text
        all_tokens_count = len(layout_response[0].outputs[0].token_ids)
        logger.info(f"layout_results: {layout_results}")

        # Stage 2: Element-level content parsing
        layout_results_list = parse_layout_string(layout_results)
        if not layout_results_list or not (layout_results.startswith("[") and layout_results.endswith("]")):
            layout_results_list = [([0, 0, *image.size], "distorted_page", [])]
        elif len(layout_results_list) > 1 and check_bbox_overlap(layout_results_list, image):
            logger.info("Falling back to distorted_page mode due to high bbox overlap")
            layout_results_list = [([0, 0, *image.size], "distorted_page", [])]

        tab_elements = []
        equ_elements = []
        code_elements = []
        text_elements = []
        figure_results = []
        reading_order = 0

        # Collect elements and group
        for bbox, label, tags in layout_results_list:
            try:
                if label == "distorted_page":
                    x1, y1, x2, y2 = 0, 0, *image.size
                    pil_crop = image
                else:
                    # get coordinates in the original image
                    x1, y1, x2, y2 = process_coordinates(bbox, image)
                    # crop the image
                    pil_crop = image.crop((x1, y1, x2, y2))

                if pil_crop.size[0] > 3 and pil_crop.size[1] > 3:
                    if label == "fig":
                        figure_filename = save_figure_to_local(pil_crop, save_dir, image_name, reading_order)
                        figure_results.append(
                            {
                                "label": label,
                                "text": f"![Figure](figures/{figure_filename})",
                                "figure_path": f"figures/{figure_filename}",
                                "bbox": [x1, y1, x2, y2],
                                "reading_order": reading_order,
                                "tags": tags,
                            }
                        )
                    else:
                        # Prepare element information
                        element_info = {
                            "crop": pil_crop,
                            "label": label,
                            "bbox": [x1, y1, x2, y2],
                            "reading_order": reading_order,
                            "tags": tags,
                        }
                        if label == "tab":
                            tab_elements.append(element_info)
                        elif label == "equ":
                            equ_elements.append(element_info)
                        elif label == "code":
                            code_elements.append(element_info)
                        else:
                            text_elements.append(element_info)

                reading_order += 1

            except Exception as e:
                print(f"Error processing bbox with label {label}: {str(e)}")
                continue

        recognition_results = figure_results.copy()

        if tab_elements:
            results, tokens_count = self.process_element_batch(tab_elements, dolphin_prompt["table"])
            recognition_results.extend(results)
            all_tokens_count += tokens_count

        if equ_elements:
            results, tokens_count = self.process_element_batch(equ_elements, dolphin_prompt["formula"])
            recognition_results.extend(results)
            all_tokens_count += tokens_count

        if code_elements:
            results, tokens_count = self.process_element_batch(code_elements, dolphin_prompt["code"])
            recognition_results.extend(results)
            all_tokens_count += tokens_count

        if text_elements:
            results, tokens_count = self.process_element_batch(text_elements, dolphin_prompt["text"])
            recognition_results.extend(results)
            all_tokens_count += tokens_count

        recognition_results.sort(key=lambda x: x.get("reading_order", 0))

        return recognition_results, all_tokens_count

    def process_element_batch(self, elements, prompt, max_batch_size=None):
        """Process elements of the same type in batches"""
        results = []
        tokens_count = 0

        # Determine batch size
        batch_size = len(elements)
        if max_batch_size is not None and max_batch_size > 0:
            batch_size = min(batch_size, max_batch_size)

        # Process in batches
        for i in range(0, len(elements), batch_size):
            batch_elements = elements[i : i + batch_size]
            crops_list = [elem["crop"] for elem in batch_elements]

            # Use the same prompt for all elements in the batch
            prompts_list = [prompt] * len(crops_list)

            # Batch inference
            batch_response = self.model_infer(crops_list, prompts_list)
            batch_results = [response.outputs[0].text for response in batch_response]
            tokens_count += sum(len(response.outputs[0].token_ids) for response in batch_response)

            # Add results
            for j, result in enumerate(batch_results):
                elem = batch_elements[j]
                results.append(
                    {
                        "label": elem["label"],
                        "bbox": elem["bbox"],
                        "text": result.strip(),
                        "reading_order": elem["reading_order"],
                        "tags": elem["tags"],
                    }
                )
                # logger.info(f"batch_results[{j}]: {result.strip()}")

        return results, tokens_count

    def model_infer(self, images: list[Image], questions: list[str]):
        messages = [
            [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "image": resize_img(image),
                        },
                        {"type": "text", "text": question},
                    ],
                }
            ]
            for image, question in zip(images, questions)
        ]

        prompts = self.processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        image_inputs, video_inputs = process_vision_info(messages)

        inputs = [
            {
                "prompt": prompt,
                "multi_modal_data": {
                    "image": image_input,
                },
            }
            for prompt, image_input in zip(prompts, image_inputs)
        ]

        responses = self.engine.generate(inputs, self.sampling_params, lora_request=self.lora_request)
        # for response in responses:
        #     logger.info(f"response: {response.outputs[0].text}")
        return responses
