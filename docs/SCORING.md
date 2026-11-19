# Scoring and parsing

Version: space-primary-strict-secondary-v2.

Primary: reuse parse_answer_from_response from the supplied QA_Agent, with only unused self removed. It selects the last regex brace-delimited object, parses JSON, accepts answer or a single alternative key, and converts int-convertible values using int(). Compare its result directly to the gold value, as evaluate_qas.py does. This deliberately preserves permissive behaviours (including string numbers, booleans and float coercion) for transparent comparison. Do not present this as a recommended general parser.

Only completed Responses outputs enter scoring. Their visible message output_text is supplied to the parser; no internal reasoning metadata is used. An ordinary unparseable answer returning None counts incorrect among completed responses, matching the original evaluator. If the original parser itself raises, record the exception and block a complete-pool score rather than hiding it.

Secondary: the strict parser requires all JSON answer values to be agreeing integers 1–4. It flags strings, booleans, conflicts or absent answer keys. It never replaces the primary parser. scores.csv includes both predictions and correctness fields plus status/completion/error indicators.

Summary: upstream_accuracy_full_pool is reported only when every expected item has a completed response and no official-parser exception. Otherwise it is null. An explicitly named correct-over-expected lower bound and all missing/error/invalid counts are reported. Strict valid-only accuracy is diagnostic and must not be quoted as full-pool accuracy. All rates are 0–1; multiply by 100 when reporting percentages.

No automatic retries. All HTTP failures, timeouts and ambiguous interrupted attempts are retained. An archived request without a raw response is not automatically resent because the service may have processed it. A subsequent audited recovery policy would require implementation, attempt IDs and supervisor review; it is not silently supplied here. Wrong or malformed completed answers are never regenerated as replacements. Repeated runs 2–5 are planned observations, not replacements for run 1.

The first formal response is the proposed human advice. Before human presentation, require a valid option and apply the agreed stability criteria; primary benchmark scoring quirks must not cause malformed advice to be shown to participants.
