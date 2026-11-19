# Upstream reconciliation

Source reviewed: supplied ml-space-benchmark-main archive, 2026-11-19. No .git directory; exact commit remains unresolved. Six original file hashes are in audit/upstream_offline_results.json. File hashes identify content but do not prove a Git commit.

Call chain: evaluate_qas.py -> QA_Agent.get_prediction -> utils/model.py -> utils/openai_api.py -> chat.completions.create. Per-item reset creates independent input. The answer argument is logged after the model response, not placed in model messages. The full JSON record pool is evaluated with a default 8 workers.

## Reuse and changes

- space_adapter.py adapts the original question parsing branch; source-order control flow is retained. Changes: resolve relative image paths under an explicit root, reject out-of-root paths, reject unsupported video, supply model/detail directly.
- vendor/space_functions.py extracts encode_image, is_int and parse_answer_from_response. Only the unused parser self parameter is removed; Python AST formatting changes are cosmetic.
- Original JPEG encoder is used. The imageio RGB reader is replaced by direct Pillow RGB conversion. The original source's encoder and supplied pool were compared offline using a substitute decoder, not a reproduced imageio installation.
- Original image_detail=low retained. Original GPT QA max_tokens=4096, temperature=0.5 and frequency_penalty=0 are historical values only, NOT silently transferred to the unresolved new model.
- Responses content typing replaces the original mixed strings/image dictionaries. New model/endpoint compatibility needs live testing.
- Original parser/equality score is primary; strict diagnostics are secondary. Original exception retries are replaced with explicit no-auto-retry logging, pending policy review.
- New logging stores actual request/response data and versions; no credentials in archives.

No original source files are modified. Apple notices and license are retained for adapted/extracted code. No claim of reproducing original model accuracies or every published setting is made.

## Offline evidence

- check_upstream_offline.py: selected original functions with fake model/dialog/image objects; first two records per category; gold-label mutation leaves model messages unchanged.
- verify_parity.py: all source question lists, ordered text and JPEG payloads compared with the original loader/encoder path using a substituted RGB decoder. Original parser compared on 15 representative response strings, including malformed/permissive cases.
- tests/: network-body label isolation, source-folder category mapping, ordering, parsing, blocked live config, failure/resume protection and primary denominator checks.

Outstanding: exact upstream commit, actual model/account access/settings, live technical testing, recovery decision and candidate/stability protocol. upstream_implementation_checked=true means this reconciliation is complete; it does not mean other gates are satisfied.
