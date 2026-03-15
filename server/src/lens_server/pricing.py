from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal

ReleaseStage = Literal["stable", "preview"]


@dataclass(frozen=True)
class PricingRule:
    input_per_million: Decimal
    output_per_million: Decimal


@dataclass(frozen=True)
class LongContextPricing:
    threshold_tokens: int
    rule: PricingRule


@dataclass(frozen=True)
class ModelPricing:
    canonical_id: str
    default_rule: PricingRule
    release_stage: ReleaseStage = "stable"
    match_prefixes: tuple[str, ...] = ()
    long_context: LongContextPricing | None = None

    def matches(self, model: str) -> bool:
        prefixes = (self.canonical_id, *self.match_prefixes)
        return any(model == prefix or model.startswith(prefix) for prefix in prefixes)

    def resolve_rule(self, prompt_tokens: int = 0) -> PricingRule:
        if self.long_context and prompt_tokens > self.long_context.threshold_tokens:
            return self.long_context.rule
        return self.default_rule


@dataclass(frozen=True)
class ProviderPricing:
    stable_models: tuple[ModelPricing, ...] = ()
    preview_models: tuple[ModelPricing, ...] = ()

    def all_models(self) -> tuple[ModelPricing, ...]:
        return self.stable_models + self.preview_models

    def models_for_stage(
        self, release_stage: ReleaseStage | None = None
    ) -> tuple[ModelPricing, ...]:
        if release_stage == "stable":
            return self.stable_models
        if release_stage == "preview":
            return self.preview_models
        return self.all_models()


PRICING_CATALOG: dict[str, ProviderPricing] = {
    "openai": ProviderPricing(
        stable_models=(
            ModelPricing(
                canonical_id="gpt-5.4",
                default_rule=PricingRule(Decimal("2.50"), Decimal("15.00")),
            ),
            ModelPricing(
                canonical_id="gpt-5-mini",
                default_rule=PricingRule(Decimal("0.25"), Decimal("2.00")),
            ),
            ModelPricing(
                canonical_id="gpt-4o",
                default_rule=PricingRule(Decimal("2.50"), Decimal("10.00")),
            ),
            ModelPricing(
                canonical_id="gpt-4o-mini",
                default_rule=PricingRule(Decimal("0.15"), Decimal("0.60")),
            ),
        )
    ),
    "anthropic": ProviderPricing(
        stable_models=(
            ModelPricing(
                canonical_id="claude-opus-4-6",
                default_rule=PricingRule(Decimal("5.00"), Decimal("25.00")),
            ),
            ModelPricing(
                canonical_id="claude-sonnet-4-6",
                default_rule=PricingRule(Decimal("3.00"), Decimal("15.00")),
            ),
            ModelPricing(
                canonical_id="claude-haiku-4-5",
                default_rule=PricingRule(Decimal("1.00"), Decimal("5.00")),
                match_prefixes=("claude-haiku-4-5-20251001",),
            ),
            ModelPricing(
                canonical_id="claude-opus-4-5",
                default_rule=PricingRule(Decimal("5.00"), Decimal("25.00")),
            ),
            ModelPricing(
                canonical_id="claude-sonnet-4-5",
                default_rule=PricingRule(Decimal("3.00"), Decimal("15.00")),
                long_context=LongContextPricing(
                    threshold_tokens=200_000,
                    rule=PricingRule(Decimal("6.00"), Decimal("22.50")),
                ),
            ),
        )
    ),
    "gemini": ProviderPricing(
        stable_models=(
            ModelPricing(
                canonical_id="gemini-2.5-pro",
                default_rule=PricingRule(Decimal("1.25"), Decimal("10.00")),
                long_context=LongContextPricing(
                    threshold_tokens=200_000,
                    rule=PricingRule(Decimal("2.50"), Decimal("15.00")),
                ),
            ),
            ModelPricing(
                canonical_id="gemini-2.5-flash",
                default_rule=PricingRule(Decimal("0.30"), Decimal("2.50")),
            ),
            ModelPricing(
                canonical_id="gemini-2.5-flash-lite",
                default_rule=PricingRule(Decimal("0.10"), Decimal("0.40")),
            ),
            ModelPricing(
                canonical_id="gemini-2.0-flash",
                default_rule=PricingRule(Decimal("0.10"), Decimal("0.40")),
            ),
            ModelPricing(
                canonical_id="gemini-1.5-flash",
                default_rule=PricingRule(Decimal("0.075"), Decimal("0.30")),
            ),
            ModelPricing(
                canonical_id="gemini-1.5-pro",
                default_rule=PricingRule(Decimal("1.25"), Decimal("5.00")),
            ),
        ),
        preview_models=(
            ModelPricing(
                canonical_id="gemini-3.1-pro-preview",
                default_rule=PricingRule(Decimal("2.00"), Decimal("12.00")),
                release_stage="preview",
                long_context=LongContextPricing(
                    threshold_tokens=200_000,
                    rule=PricingRule(Decimal("4.00"), Decimal("18.00")),
                ),
            ),
            ModelPricing(
                canonical_id="gemini-3.1-flash-lite-preview",
                default_rule=PricingRule(Decimal("0.25"), Decimal("1.50")),
                release_stage="preview",
            ),
        ),
    ),
}


def list_supported_models(provider: str, release_stage: ReleaseStage | None = None) -> list[str]:
    provider_catalog = PRICING_CATALOG.get(provider.lower())
    if not provider_catalog:
        return []
    return [model.canonical_id for model in provider_catalog.models_for_stage(release_stage)]


def resolve_pricing_model(provider: str, model: str) -> ModelPricing | None:
    provider_catalog = PRICING_CATALOG.get(provider.lower())
    if not provider_catalog:
        return None

    for entry in provider_catalog.all_models():
        if entry.matches(model):
            return entry
    return None


def resolve_pricing_rule(provider: str, model: str, prompt_tokens: int = 0) -> PricingRule | None:
    pricing_model = resolve_pricing_model(provider, model)
    if pricing_model is None:
        return None
    return pricing_model.resolve_rule(prompt_tokens=prompt_tokens)


def calculate_cost_usd(
    provider: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> float:
    rule = resolve_pricing_rule(provider, model, prompt_tokens=prompt_tokens)
    if rule is None:
        return 0.0

    prompt_cost = Decimal(prompt_tokens) * rule.input_per_million / Decimal(1_000_000)
    completion_cost = Decimal(completion_tokens) * rule.output_per_million / Decimal(1_000_000)
    total = prompt_cost + completion_cost
    return float(total.quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP))
