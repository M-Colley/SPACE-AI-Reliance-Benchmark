# Derived from SPACE, Copyright (C) 2025 Apple Inc. All Rights Reserved.
# See APPLE_LICENSE.txt. Extracted functions retain original semantics.
# parse_answer_from_response: only unused self argument removed.
import base64
import json
import re
from io import BytesIO
import numpy as np
from PIL import Image

def encode_image(image: np.ndarray):
    buffered = BytesIO()
    image = Image.fromarray(image)
    image.save(buffered, format='JPEG')
    output = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return output

def is_int(text: str):
    try:
        int(text)
    except Exception:
        return False
    else:
        return True

def parse_answer_from_response(text: str):
    outputs = re.findall('({.*?})', text, re.DOTALL)
    if len(outputs) == 0:
        print(f'Unable to parse answer from text:\n{text}')
        return None
    output = outputs[-1].strip()
    try:
        answer_dict = json.loads(output)
    except ValueError:
        print(f'Unable to decode json from text:\n{text}')
        answer = None
    else:
        if 'answer' in answer_dict:
            answer = {'answer': answer_dict['answer']}
        elif len(answer_dict) == 1:
            answer = {'answer': list(answer_dict.values())[0]}
        else:
            print(f'Ambiguous response in text (dict without key `answer`):\n{text}')
            answer = None
    if answer is not None and answer['answer'] is None:
        answer = None
    if answer is not None and is_int(answer['answer']):
        answer['answer'] = int(answer['answer'])
    if answer is not None:
        answer = answer['answer']
    return answer
