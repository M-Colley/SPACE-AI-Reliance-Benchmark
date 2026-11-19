# SPACE AI reliability benchmarking

Undergraduate research preparation for a study of human reliance on AI advice.

**Status: preparation draft, not an approved or completed benchmark.** No model snapshot has been selected or verified. This adapter preserves the question array in the local dataset, but is independently written and has NOT yet been compared with SPACE's original loader, model wrapper and scorer. Complete `docs/UPSTREAM.md` before claiming original-loader reuse or starting live testing.

## Scope

Four visual QA datasets: MRT_vision, PTT_vision, JLO_vision and MPFB_vision. The inspected local release contains 688, 400, 200 and 200 records respectively (1,488 total). These are source records, not necessarily independent stimuli. All source records are retained for first-pass benchmarking; image families and option-order variants require separate grouping before pilot selection. Source task labels are not trusted because all four files report `MRT (vision)`; category comes from the source directory.

## Files

- `benchmark.py`: offline inventory, independent-question concurrent Responses requests, raw-response logging and local scoring.
- `config.json`: draft settings; null values and verification flags intentionally block live runs.
- `docs/PROMPTS.md`: source wording and transformation policy.
- `docs/SCORING.md`: parsing, errors and denominators.
- `docs/RUN_PLAN.md`: technical, full-pool and repeated-run stages.
- `docs/UPSTREAM.md`: unresolved upstream-reuse checklist.
- `docs/CONFIGURATION.md`: every setting explained.
- `manifests/`: generated record IDs and hashes, without question text, images or answer keys.
- `tests/test_protocol.py`: offline tests including a gold-label mutation test.
- `requirements.txt`: no external packages; uses the Python standard library.

## Local setup

Keep the dataset outside the repository. Set its location at each command; no personal absolute paths are committed. Python 3.9+ is required. From this repository's directory:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m unittest discover -s tests -v
python benchmark.py audit --data-root /path/to/SPACE_data_release
```

Audit makes no API calls. It creates public manifests and a local-only preview in `local/request_preview.json`. Images in the preview are replaced by a placeholder; actual live requests contain image bytes. The preview may contain copyrighted question wording and must not be posted automatically.

## Before a live run

1. Compare with upstream source and record its commit; reuse its loader or document a reviewed adapter deviation.
2. Verify a real dated model snapshot and every model-specific parameter. Resolve output token allowance by technical checks, not by forcing an answer-only limit.
3. Finalise parsing, failure handling, pool scope, and prompt policy. Share model ID, settings and protocol with the supervisor.
4. Commit code and config in a public GitHub/OSF repository BEFORE live testing. After technical-only changes, freeze and publish the final full-run commit BEFORE the full run.
5. Put `OPENAI_API_KEY` in the local environment, never in any file submitted to this repository.
6. Use separate technical and formal run IDs. Do not upload the local dataset, requests, raw responses or keys by dragging the entire working folder into a browser. Browser uploads are not protected by `.gitignore` rules.

The draft config cannot run API calls. After all checks, the actual model ID/token limit/upstream commit are entered, flags truthfully updated and `status` changed to `ready`. These are declarations of completed checks, not switches to bypass missing work.

```sh
python benchmark.py run --data-root /path/to/SPACE_data_release --phase technical --run-id technical-001
python benchmark.py score --data-root /path/to/SPACE_data_release --run-id technical-001
# Only AFTER final protocol freeze and publication:
python benchmark.py run --data-root /path/to/SPACE_data_release --phase full --run-id full-001
python benchmark.py score --data-root /path/to/SPACE_data_release --run-id full-001
```

The run command makes paid API calls. It runs three independent requests concurrently by default; this is NOT the Batch API. It archives each exact request locally (without credentials), raw response text, request ID, configuration, dataset hashes, code commit and environment. Resume with the identical command: already logged items, including failures, are not resubmitted. Do not make a new run ID simply to retry failed items; see the failure policy.

## Provenance and licensing

Source: https://github.com/apple-aiml-research/ml-space-benchmark (redirected from apple/ml-space-benchmark).
Paper: Ramakrishnan, Wijmans, Krähenbühl and Koltun (2025), Does Spatial Cognition Emerge in Frontier Models?, ICLR.
The upstream README identifies separate Apple Sample Code and CC-BY-NC-ND data licenses. Review the exact license files and required notices before copying source or redistributing stimuli. No upstream source code, images, complete question text or answer keys are redistributed in this draft. No claim of identical published evaluation settings is made.

## Limitations

No API compatibility or cost test has been performed. Exact-duplicate detection is not semantic deduplication. Single-pass record-weighted accuracy is distinct from unique-question accuracy. The strict parser is a proposed local rule, not yet verified against the published scorer. Pilot selection and the five-run stability filter remain to be finalised; repeated-run collection is supported, but the stability-selection script is not implemented here.
