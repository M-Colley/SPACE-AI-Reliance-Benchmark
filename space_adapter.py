# Adapted from SPACE evaluate_qas.py, Copyright (C) 2025 Apple Inc.
# See vendor/APPLE_LICENSE.txt. Original segment-order logic retained.
# Changes: local path resolution, explicit unsupported-video error, direct Pillow RGB decoding.
from pathlib import Path
import numpy as np
from PIL import Image
from vendor.space_functions import encode_image

def get_image_as_message(image_path, model_name, image_detail):
    with Image.open(image_path) as im:
        image = np.array(im.convert('RGB'))
    encoded = encode_image(image)
    return {'type':'image_url','image_url':{'url':'data:image/jpeg;base64,'+encoded,'detail':image_detail}}

def get_video_as_messages(*args, **kwargs):
    raise ValueError('Video input is outside the four selected visual QA datasets')

def load_question_content(question, data_root, model_name, image_detail):
    if isinstance(question, list):
        question_content = []
        for q in question:
            if q.startswith('IMAGE:'):
                image_path = q[len('IMAGE:'):]
                prefix = 'data/SPACE_data_release/'
                if not image_path.startswith(prefix):
                    raise ValueError('Unexpected source image path')
                root = Path(data_root).resolve()
                path = (root / image_path[len(prefix):]).resolve()
                if root not in path.parents or not path.is_file():
                    raise ValueError('Missing or out-of-root image')
                image_path = str(path)
                message = get_image_as_message(image_path=image_path, model_name=model_name, image_detail=image_detail)
                question_content.append(message)
            elif q.startswith('VIDEO:'):
                video_path = q[len('VIDEO:'):]
                video_messages = get_video_as_messages(video_path, model_name=model_name, subsampling_factor=1, image_detail=image_detail)
                question_content.extend(video_messages)
            else:
                question_content.append(q)
    elif isinstance(question, str):
        question_content = question
    else:
        raise ValueError(f'Unable to parse question_content with type: {type(question)}')
    return question_content
