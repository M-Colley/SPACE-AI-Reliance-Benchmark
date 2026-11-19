# Configuration fields

Delivered config is review_pending_model_and_parameters; live execution is intentionally blocked.

- model_snapshot: null pending verified exact ID. The current guard requires a date in the ID to reflect Mark's request. If a non-dated fixed-version alternative is explicitly agreed, revise the guard and document evidence; never invent an ID.
- reasoning_effort: null pending decision. Null omits the parameter; it does NOT set reasoning to none. Medium was the user's initial preference.
- max_output_tokens: null pending adequate model-supported budget. Do not set to 1 based on an option-only final answer.
- image_detail: low to align with original GPT QA configuration. Any later change must be documented before formal collection.
- concurrency: 3 independent requests, conservative proposed throughput; no shared context. Use one process per run ID.
- timeout_seconds: 180 proposed. Timeouts remain unresolved technical events, not assumed unprocessed requests.
- upstream_commit: null pending actual source commit. Source SHA-256 values are recorded separately.
- upstream_implementation_checked: true means source comparison and documented adapter reconciliation completed, not model API verification.
- model_settings_verified: false until model access, parameter and endpoint checks complete.
- failure_policy_approved: false until the no-automatic-retry proposal or an implemented alternative is agreed.
- status: ready only after required checks. Keep current review status while sharing with Mark.
- protocol_version/parser_version: review-2 / space-primary-strict-secondary-v2.

No temperature, top_p, seed, tools, previous_response_id, additional system instructions or explicit reasoning mode are sent. Omitted settings use service defaults; do not describe them as experimentally set to zero. store=false is requested but is not a claim about zero provider retention. Exact code/config, Python/OS/dependency versions and input hashes are recorded per run.

The model request whitelist does not forward the entire config, source record, answer key or metadata to the API. OPENAI_API_KEY is read only from the local environment, never from config.json.
