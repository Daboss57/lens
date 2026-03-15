from lens_server.pricing import (
    calculate_cost_usd,
    list_supported_models,
    resolve_pricing_model,
    resolve_pricing_rule,
)


def test_resolve_pricing_rule_matches_current_openai_prefix_variants() -> None:
    rule = resolve_pricing_rule("openai", "gpt-5.4-2026-03-01")
    assert rule is not None


def test_resolve_pricing_rule_matches_current_anthropic_aliases() -> None:
    rule = resolve_pricing_rule("anthropic", "claude-sonnet-4-6-20260301")
    assert rule is not None


def test_resolve_pricing_rule_matches_current_gemini_preview_models() -> None:
    rule = resolve_pricing_rule("gemini", "gemini-3.1-pro-preview-2026-03")
    assert rule is not None


def test_resolve_pricing_model_exposes_preview_stage() -> None:
    pricing_model = resolve_pricing_model("gemini", "gemini-3.1-pro-preview")
    assert pricing_model is not None
    assert pricing_model.release_stage == "preview"


def test_list_supported_models_can_filter_release_stage() -> None:
    assert "gemini-2.5-pro" in list_supported_models("gemini", "stable")
    assert "gemini-3.1-pro-preview" in list_supported_models("gemini", "preview")


def test_calculate_cost_usd_for_gpt_5_4() -> None:
    assert calculate_cost_usd("openai", "gpt-5.4", 1000, 500) == 0.01


def test_long_context_pricing_applies_for_gemini_2_5_pro() -> None:
    assert calculate_cost_usd("gemini", "gemini-2.5-pro", 250000, 1000) == 0.64


def test_long_context_pricing_applies_for_claude_sonnet_4_5() -> None:
    assert calculate_cost_usd("anthropic", "claude-sonnet-4-5", 210000, 1000) == 1.2825


def test_calculate_cost_usd_returns_zero_for_unknown_model() -> None:
    assert calculate_cost_usd("openai", "unknown-model", 100, 20) == 0.0
