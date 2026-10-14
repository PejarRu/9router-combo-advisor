#!/usr/bin/env python3
import json
import unittest
from unittest.mock import patch
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
import advisor


class AdvisorTest(unittest.TestCase):
    def model(self, **kw):
        return {"id": kw.pop("id"), "provider": kw.pop("provider", "openrouter"),
                "qualityScore": kw.pop("qualityScore", 0), "price": kw.pop("price", {"free": False}),
                "context": kw.pop("context", 0), "subscription": kw.pop("subscription", False), **kw}

    def test_free_smart_only_free_models(self):
        models = [
            self.model(id="openrouter/x:free", price={"free": True}, qualityScore=10),
            self.model(id="openrouter/y", price={"free": False}, qualityScore=100),
        ]
        proposal = advisor.propose(models)
        self.assertEqual(proposal["free-smart"], ["openrouter/x:free"])

    def test_venice_smart_only_venice(self):
        models = [
            self.model(id="venice/a", provider="venice", qualityScore=10),
            self.model(id="openrouter/x", provider="openrouter", qualityScore=100),
        ]
        proposal = advisor.propose(models)
        self.assertEqual(proposal["venice-smart"], ["venice/a"])

    def test_venice_cheap_sorts_by_price(self):
        models = [
            self.model(id="venice/expensive", provider="venice", price={"free": False, "input": 10, "output": 10}, qualityScore=100),
            self.model(id="venice/cheap", provider="venice", price={"free": False, "input": 1, "output": 1}, qualityScore=50),
        ]
        proposal = advisor.propose(models)
        self.assertEqual(proposal["venice-cheap"], ["venice/cheap", "venice/expensive"])

    def test_free_fast_only_free(self):
        models = [
            self.model(id="openrouter/x:free", price={"free": True}, qualityScore=1),
            self.model(id="openrouter/y", price={"free": False}, qualityScore=100),
        ]
        proposal = advisor.propose(models)
        self.assertEqual(proposal["free-fast"], ["openrouter/x:free"])

    def test_gemini_only_gemini_provider(self):
        models = [
            self.model(id="gemini/a", provider="gemini", qualityScore=10),
            self.model(id="openrouter/x", provider="openrouter", qualityScore=100),
        ]
        proposal = advisor.propose(models)
        self.assertEqual(proposal["gemini"], ["gemini/a"])

    def test_mistral_only_mistral_provider(self):
        models = [
            self.model(id="mistral/a", provider="mistral", qualityScore=10),
            self.model(id="openrouter/x", provider="openrouter", qualityScore=100),
        ]
        proposal = advisor.propose(models)
        self.assertEqual(proposal["mistral"], ["mistral/a"])

    def test_main_uses_real_codex_provider_then_github(self):
        models = [
            self.model(id="github/gpt-5.4-mini-free-auto", provider="github", subscription=True, qualityScore=2),
            self.model(id="github/gpt-5.6-luna", provider="github", subscription=True, qualityScore=3),
            self.model(id="github/gpt-6-luna", provider="github", subscription=True, qualityScore=4),
            self.model(id="github/gpt-4.1", provider="github", subscription=True, qualityScore=5),
            self.model(id="codex/gpt-5.5", provider="codex", subscription=True, qualityScore=8),
            self.model(id="codex/gpt-5.6-sol", provider="codex", subscription=True, qualityScore=10),
            self.model(id="codex/gpt-5.6-terra", provider="codex", subscription=True, qualityScore=99),
            self.model(id="openrouter/x", provider="openrouter", qualityScore=7),
        ]
        pool = [model["id"] for model in advisor.llm_pool("main", models)]
        self.assertEqual(pool[:3], ["codex/gpt-5.6-terra", "codex/gpt-5.5", "github/gpt-4.1"])
        proposal = advisor.propose(models)
        self.assertEqual(proposal["main"][:2], ["codex/gpt-5.6-terra", "codex/gpt-5.5"])
        self.assertEqual(len([i for i in proposal["main"] if i.startswith("codex/")]), 2)
        self.assertEqual(len([i for i in proposal["main"] if i.startswith("github/")]), 1)

    def test_jev_selects_models_and_respects_confidence(self):
        models = [
            self.model(id="venice/a", provider="venice", name="Venice A", description="Venice model A", qualityScore=50, price={"known": False, "free": False, "input": 0, "output": 0}),
            self.model(id="venice/b", provider="venice", name="Venice B", description="Venice model B", qualityScore=40, price={"known": False, "free": False, "input": 0, "output": 0}),
            self.model(id="venice/c", provider="venice", name="Venice C", description="Venice model C", qualityScore=30, price={"known": False, "free": False, "input": 0, "output": 0}),
        ]

        def high_confidence(url, model, key, state, questions):
            options = questions["model"]["criteria"]
            choice = next(iter(options))
            return {"model": {"choice": choice, "confidence": 0.95, "probabilities": {choice: 0.95}}}

        with patch.object(advisor, "jev_channel", return_value=("http://example.invalid", "jev-latest", "key", "typesafe")), patch.object(
            advisor, "jev_request", side_effect=high_confidence
        ):
            proposals, traces = advisor.select_with_jev(models)
        self.assertEqual(proposals["venice-smart"], ["venice/a", "venice/b", "venice/c"])
        self.assertEqual(traces["combos"]["venice-smart"]["backfilled"], 0)
        self.assertEqual(traces["combos"]["free-smart"]["positions"], [])

        def low_confidence(url, model, key, state, questions):
            options = questions["model"]["criteria"]
            choice = next(iter(options))
            return {"model": {"choice": choice, "confidence": 0.2, "probabilities": {choice: 0.2}}}

        with patch.object(advisor, "jev_channel", return_value=("http://example.invalid", "jev-latest", "key", "typesafe")), patch.object(
            advisor, "jev_request", side_effect=low_confidence
        ):
            proposals, traces = advisor.select_with_jev(models)
        self.assertEqual(proposals["venice-smart"], ["venice/a", "venice/b", "venice/c"])
        self.assertEqual(traces["combos"]["venice-smart"]["backfilled"], 3)

    def test_or_benchmarks_match_and_composite(self):
        import tempfile
        models = [
            self.model(id="openrouter/xiaomi/mimo-v2.5", provider="openrouter", qualityScore=10),
            self.model(id="codex_1/gpt-5.6-sol", provider="codex_1", subscription=True, qualityScore=10),
            self.model(id="venice/unknown", provider="venice", qualityScore=10),
        ]
        benchmarks = {"openrouter/xiaomi/mimo-v2.5": 90, "codex_1/gpt-5.6-sol": 85}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(benchmarks, f)
            bench_path = f.name
        try:
            advisor.apply_benchmarks(models, bench_path)
            self.assertEqual(models[0]["benchmarkScore"], 90)
            self.assertEqual(models[1]["benchmarkScore"], 85)
            self.assertIsNone(models[2].get("benchmarkScore"))
        finally:
            import os
            os.unlink(bench_path)

    def test_chev_prioritizes_value(self):
        models = [
            self.model(id="openrouter/a:free", price={"free": True}, qualityScore=5),
            self.model(id="openrouter/b", price={"free": False, "input": 1, "output": 1}, qualityScore=100),
        ]
        proposal = advisor.propose(models)
        self.assertEqual(proposal["free-smart"][0], "openrouter/a:free")

    def test_prioritize_value_tools_keeps_tools_first(self):
        models = [
            self.model(id="openrouter/a", qualityScore=10),
            self.model(id="openrouter/b", qualityScore=5),
        ]
        proposal = {"main": ["openrouter/a", "openrouter/b"]}
        result = advisor.prioritize_value_tools(proposal, models)
        self.assertEqual(result["main"][0], "openrouter/a")

    def test_free_smart_does_not_restore_named_stale_models(self):
        models = [self.model(id="openrouter/alive:free", price={"free": True}, qualityScore=10)]
        result = advisor.prioritize_value_tools(
            {"free-smart": ["openrouter/qwen/qwen3.8-27b:free", "openrouter/alive:free"]},
            models,
        )
        self.assertEqual(result["free-smart"], ["openrouter/alive:free"])

    def test_free_smart_requires_a_successful_smoke(self):
        models = [self.model(id="openrouter/a:free", price={"free": True}, qualityScore=10)]
        proposals = {"free-smart": ["openrouter/a:free"]}
        with patch.object(advisor, "nine_api_key", return_value="key"), patch.object(
            advisor, "probe_one", return_value=("transient", 429, "rate limit")
        ):
            advisor.run_smoke(proposals, models)
        self.assertEqual(proposals["free-smart"], [])

    def test_free_smart_keeps_healthy_fallback_after_dead_model(self):
        dead = "openrouter/qwen/qwen3.8-27b:free"
        alive = "openrouter/cohere/north-mini-code:free"
        models = [
            self.model(id=dead, price={"free": True}, qualityScore=90),
            self.model(id=alive, price={"free": True}, qualityScore=20),
        ]
        proposals = {"free-smart": [dead, alive]}

        def probe(model_id, key, base):
            return ("dead", 404, "not found") if model_id == dead else ("alive", 200, "ok")

        with patch.object(advisor, "nine_api_key", return_value="key"), patch.object(advisor, "probe_one", side_effect=probe):
            advisor.run_smoke(proposals, models)
        self.assertEqual(proposals["free-smart"], [alive])

    def test_extra_smart_excludes_free_openrouter_models(self):
        models = [
            self.model(id="codex/gpt-6.1-sol", provider="codex", subscription=True, qualityScore=80),
            self.model(id="openrouter/paid", price={"free": False}, qualityScore=70),
            self.model(id="openrouter/free:free", price={"free": True}, qualityScore=100),
        ]
        self.assertNotIn("openrouter/free:free", [model["id"] for model in advisor.llm_pool("extra-smart", models)])

    def test_main_does_not_expand_beyond_its_known_good_routes(self):
        models = [
            self.model(id="codex/a", provider="codex", subscription=True),
            self.model(id="github/b", provider="github", subscription=True),
            self.model(id="codex/c", provider="codex", subscription=True),
        ]
        proposals = {"main": ["codex/a", "github/b"]}
        with patch.object(advisor, "nine_api_key", return_value="key"):
            advisor.run_smoke(proposals, models)
        self.assertEqual(proposals["main"], ["codex/a", "github/b"])

    def test_extra_smart_retains_paid_frontier_fallbacks(self):
        paid = "openrouter/frontier"
        models = [self.model(id=paid, price={"free": False}, qualityScore=90)]
        proposals = {"extra-smart": [paid]}
        with patch.object(advisor, "nine_api_key", return_value="key"), patch.object(advisor, "probe_one") as probe:
            advisor.run_smoke(proposals, models)
        probe.assert_not_called()
        self.assertEqual(proposals["extra-smart"], [paid])

    def test_free_fast_excludes_safety_endpoint_and_uses_probe_latency(self):
        fast = "openrouter/fast:free"
        slow = "openrouter/slow:free"
        safety = "openrouter/nvidia/nemotron-3.5-content-safety:free"
        models = [
            self.model(id=fast, price={"free": True}, qualityScore=10),
            self.model(id=slow, price={"free": True}, qualityScore=90),
            self.model(id=safety, price={"free": True}, qualityScore=100),
        ]
        self.assertNotIn(safety, [model["id"] for model in advisor.llm_pool("free-fast", models)])
        proposals = {"free-fast": [slow, fast]}
        with patch.object(advisor, "nine_api_key", return_value="key"), patch.object(
            advisor, "probe_one", return_value=("alive", 200, "ok")
        ), patch.object(advisor.time, "monotonic", side_effect=[0, 2, 3, 3.1]):
            advisor.run_smoke(proposals, models)
        self.assertEqual(proposals["free-fast"], [fast, slow])


if __name__ == "__main__":
    unittest.main()
