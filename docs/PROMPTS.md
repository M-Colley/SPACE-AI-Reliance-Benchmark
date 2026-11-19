# Prompt and image policy

Preserve each original question array's text, order and answer-option ordering. The list-processing branch is adapted from evaluate_qas.py in space_adapter.py. Only IMAGE path resolution and unsupported-video rejection change that branch. The four selected datasets use text/image lists.

The original encode_image function is reused. Local images are read using Pillow convert(RGB), converted to an array, and encoded with the original Pillow JPEG defaults. This replaces the original imageio RGB reader; dependency versions are pinned and this is a declared difference. No resizing, cropping or annotation is added. Image detail is low, matching the supplied GPT QA configurations.

The resulting original mixed strings/image dictionaries are translated into Responses input_text/input_image objects. This changes API representation, not word order or image payload. One user message per question; no added system/developer message, examples, tool access or conversation history. The source instruction requesting step-by-step reasoning and JSON is preserved. Participants later see only the parsed advice option, not reasoning text.

The request-builder receives only the question list. Outer answer/task fields do not enter its interface. The scorer separately reads gold labels. A mutation test checks that changing gold labels leaves requests unchanged. This does not rule out answer cues embedded in the source image/text or prior model familiarity with public stimuli.

Do not upload local request previews or request archives without stimulus-license review.
