# SPACE AI reliability benchmarking

**Review version 2 — offline verified; live execution blocked pending model/settings and provenance decisions.** This repository supports preparation of an undergraduate study of human reliance on AI. It is not a completed benchmark or a claim of full reproduction of the published model results.

The implementation adapts the supplied SPACE QA loader logic, reuses the original JPEG encoder and answer parser, and adds independent Responses requests, raw-response archiving and explicit failure accounting. Original licensing notices are in vendor/.

## Scope and methods

The four local files contain MRT_vision 688, PTT_vision 400, JLO_vision 200 and MPFB_vision 200 records: 1,488 total. Category comes from the directory because source task fields are all labelled MRT (vision). All source records are retained for the first pass; they are not assumed to be independent stimulus families. IDs are zero-based row indices, pinned by source-file hashes.

Each request contains one original question with its ordered text and images. No gold label, task metadata, examples, prior question or prior answer is transmitted. Images are decoded to RGB and encoded to JPEG with the original encoder; image detail is low. Responses uses typed text/image content, a necessary interface adaptation from the supplied Chat Completions representation.

Primary scoring uses the extracted official parser and prediction == gold. A separate stricter parser flags ambiguous/unusual outputs but does not silently replace the primary score. Missing/failed requests prevent a complete-pool accuracy claim. See docs/SCORING.md.

## Files

- benchmark.py: audit, request execution, resume protection and scoring.
- space_adapter.py: adapted official question-segment loader and local image path handling.
- vendor/space_functions.py: extracted original JPEG encoder and parser, with Apple notices.
- config.json: model-specific values intentionally unresolved; live gates remain closed.
- requirements.txt: exact Pillow/numpy versions used for offline verification.
- docs/: prompting, scoring, configuration, execution, provenance and upload instructions.
- manifests/: ID/hash inventory, without question text or answer keys.
- tests/: offline tests; audit/: source-comparison tools and reports.

## Installation and offline checks

Use Python 3.12 (offline verified with Python 3.12) in a fresh environment. From the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python benchmark.py audit --data-root /path/to/SPACE_data_release
python audit/verify_parity.py /path/to/ml-space-benchmark-main /path/to/SPACE_data_release
```

None of these commands calls the model. The last command requires the inspected local upstream source. Tests use mocks; the parity check executes selected original functions and uses Pillow in place of the imageio RGB decoding dependency. See audit/parity_results.json for scope and limitations. Audit generates a local-only request preview containing question wording; do not publish local/.

## Model decision and live execution

Proposed model family: GPT-6 Astra; exact fixed model ID and settings are awaiting supervisor discussion. config.json deliberately contains null model/reasoning/output-budget values. Do not replace null with a guessed snapshot or mark review flags true to bypass incomplete work.

Before live technical testing: record the upstream commit, confirm model/endpoint/parameter access, agree the no-automatic-retry policy or implement a reviewed recovery policy, commit/publish the code and configuration, and supply OPENAI_API_KEY locally. The actual execution directory must be a Git checkout of the published code, with a clean working tree.

```sh
# Paid calls; blocked with the delivered review configuration:
python benchmark.py run --data-root /path/to/SPACE_data_release --phase technical --run-id technical-001
python benchmark.py score --data-root /path/to/SPACE_data_release --run-id technical-001
# After technical checks, freeze/publish the final configuration before:
python benchmark.py run --data-root /path/to/SPACE_data_release --phase full --run-id full-001
python benchmark.py score --data-root /path/to/SPACE_data_release --run-id full-001
```

This uses three concurrent independent ordinary Responses requests, NOT Batch API. The exact request, raw returned text, HTTP/request identifiers, code/config version, dependency versions and source hashes are archived locally. API keys are never archived. Repeat the identical run command to resume: completed, failed and potentially in-flight requests are not silently resubmitted. Run only one process for each run ID. Changed code/config/source/environment blocks resume.

Repeated-candidate collection uses `--phase repeat --candidate-ids /path/to/frozen_ids.json --repeat-number 2 --run-id candidates-r2`, then analogous numbers 3, 4, 5. IDs and scientific settings must stay identical. Candidate selection quotas and stability filtering are documented proposals, not implemented final selection procedures.

## Publication and licensing

Publish this review package as a draft now. Publish the final run commit BEFORE the formal run. A public code repository is not the later study preregistration. Do not upload data/, local/, runs/, API keys or human data. A browser upload does not apply .gitignore exclusions automatically.

SPACE source: https://github.com/apple-aiml-research/ml-space-benchmark . Paper: Ramakrishnan, Wijmans, Krähenbühl and Koltun (2025), Does Spatial Cognition Emerge in Frontier Models?, ICLR.

Adapted/extracted source is attributed in space_adapter.py and vendor/space_functions.py. Apple license and acknowledgements are retained. Original stimuli and gold keys are not redistributed; obtain them from the official source and review LICENSE_DATA before any redistribution. No license is imposed here that purports to replace Apple's terms.

## Outstanding limitations

Upstream commit is unknown for the downloaded archive (file hashes recorded). No live API, account-access, cost or actual imageio-environment verification has occurred. Dated model availability is unresolved. Network recovery and candidate/stability decisions require review. Independent human piloting, power analysis and Gorilla tasks are outside this repository's current scope.
