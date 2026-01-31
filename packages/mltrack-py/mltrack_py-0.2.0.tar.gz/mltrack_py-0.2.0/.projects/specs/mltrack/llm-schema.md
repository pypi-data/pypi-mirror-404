# LLM Tracking Canonical Schema (T6)

Purpose
- Define the canonical LLM tracking fields for mltrack.
- Remove legacy and duplicate fields (no backward compatibility).
- Provide a clear provider-to-canonical mapping for OpenAI, Anthropic, Gemini, and Bedrock.

## Canonical schema (required)
Tags
- llm.model (string, required)
- llm.provider (string, required; lowercase: openai, anthropic, gemini, bedrock, vertex_ai)

Metrics
- llm.tokens.prompt_tokens (int)
- llm.tokens.completion_tokens (int)
- llm.tokens.total_tokens (int)
- llm.cost_usd (float)
- llm.latency_ms (float)

Artifacts
- llm_inputs.json
- llm_outputs.json

## Canonical schema (optional metadata tags)
- llm.finish_reason (string)
- llm.request_id (string)
- llm.response_id (string)

Note: metadata tags are only set when a provider surfaces them.

## Canonical schema (optional provider-specific metrics)
- llm.tokens.cache_read_input_tokens (int)
- llm.tokens.cache_write_input_tokens (int)
- llm.tokens.cache_creation_input_tokens (int)
- llm.tokens.cached_content_token_count (int)
- llm.tokens.tool_use_prompt_token_count (int)

Note: optional fields are only logged when a provider returns them. We keep naming consistent under llm.tokens.* using snake_case.

## Provider-to-canonical mapping
OpenAI
- Chat Completions usage:
  - usage.prompt_tokens -> llm.tokens.prompt_tokens
  - usage.completion_tokens -> llm.tokens.completion_tokens
  - usage.total_tokens -> llm.tokens.total_tokens
- Responses API usage:
  - usage.input_tokens -> llm.tokens.prompt_tokens
  - usage.output_tokens -> llm.tokens.completion_tokens
  - usage.total_tokens -> llm.tokens.total_tokens
- Optional metadata:
  - response.id -> llm.response_id (when available)
  - response._request_id or response.request_id -> llm.request_id (SDK-specific)
  - choices[0].finish_reason -> llm.finish_reason
- Optional (if surfaced later): cached or reasoning token details can map under llm.tokens.* if needed.

Anthropic (Claude)
- message.usage.input_tokens -> llm.tokens.prompt_tokens
- message.usage.output_tokens -> llm.tokens.completion_tokens
- total = input + output -> llm.tokens.total_tokens
- message.usage.cache_creation_input_tokens -> llm.tokens.cache_creation_input_tokens (optional)
- message.usage.cache_read_input_tokens -> llm.tokens.cache_read_input_tokens (optional)
- Optional metadata:
  - message.id -> llm.response_id
  - message.stop_reason -> llm.finish_reason

Gemini (Google AI)
- usageMetadata.promptTokenCount -> llm.tokens.prompt_tokens
- usageMetadata.candidatesTokenCount -> llm.tokens.completion_tokens
- total = prompt + candidates -> llm.tokens.total_tokens
- usageMetadata.cachedContentTokenCount -> llm.tokens.cached_content_token_count (optional)
- usageMetadata.toolUsePromptTokenCount -> llm.tokens.tool_use_prompt_token_count (optional)
- Optional metadata:
  - response.responseId / response.response_id -> llm.response_id (when available)
  - candidates[0].finishReason -> llm.finish_reason

Vertex AI (Google)
- usageMetadata.promptTokenCount -> llm.tokens.prompt_tokens
- usageMetadata.candidatesTokenCount -> llm.tokens.completion_tokens
- total = prompt + candidates -> llm.tokens.total_tokens
- usageMetadata.cachedContentTokenCount -> llm.tokens.cached_content_token_count (optional)
- usageMetadata.toolUsePromptTokenCount -> llm.tokens.tool_use_prompt_token_count (optional)
- Optional metadata:
  - response.responseId / response.response_id -> llm.response_id (when available)
  - candidates[0].finishReason -> llm.finish_reason

AWS Bedrock (Converse)
- usage.inputTokens -> llm.tokens.prompt_tokens
- usage.outputTokens -> llm.tokens.completion_tokens
- usage.totalTokens -> llm.tokens.total_tokens
- usage.cacheReadInputTokens -> llm.tokens.cache_read_input_tokens (optional)
- usage.cacheWriteInputTokens -> llm.tokens.cache_write_input_tokens (optional)
- Optional metadata:
  - response.requestId / response.request_id -> llm.request_id (when available)
  - response.stopReason -> llm.finish_reason

## Current backend emission (audit)
From src/mltrack/llm.py:
- Tags:
  - llm.provider
  - llm.model
- Metrics:
  - llm.latency_ms
  - llm.tokens.prompt_tokens
  - llm.tokens.completion_tokens
  - llm.tokens.total_tokens
  - llm.cost_usd
  - llm.tokens.<provider_specific> (cache/tool tokens when present)
- Artifacts:
  - llm_inputs.json, llm_outputs.json

## Current UI consumption (audit)
UI references in ui/components and ui/app:
- Tags (LLM-specific): llm.model, llm.provider
- Metrics (LLM-specific):
  - llm.cost_usd
  - llm.tokens.prompt_tokens
  - llm.tokens.completion_tokens
  - llm.tokens.total_tokens
  - llm.latency_ms

## Removal list (no backward compatibility)
LLM tracking should stop emitting the following legacy fields:
- Tags: mltrack.type, mltrack.task, mltrack.framework, mltrack.provider, mltrack.algorithm (from LLM paths)
- Params: llm.<param> (drop or move under a new explicit namespace if needed later)
- Metrics: llm.total_cost, llm.total_tokens, llm.prompt_tokens, llm.completion_tokens, llm.tokens.input_tokens, llm.tokens.output_tokens, llm.latency
- Aggregates: llm.conversation.* (remove unless we explicitly re-scope it later)

UI should remove fallbacks that reference legacy keys and rely only on canonical llm.* fields.

## Next steps (tracked in Beads)
- T6: Update telemetry spec (this doc).
- T7: Provider usage adapters (metadata + usage normalization).
- T8: Pricing + cost engine.
- T9: Streaming + async tracking.
- T10: UI LLM analytics enhancements.
- T11: Data quality tests with provider fixtures.
