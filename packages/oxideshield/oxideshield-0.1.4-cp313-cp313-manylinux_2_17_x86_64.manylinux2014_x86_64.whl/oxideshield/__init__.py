# OxideShield - High-performance LLM security toolkit
# This module is implemented in Rust using PyO3

from .oxideshield import (
    # Core types
    PatternMatcher,
    Match,
    Severity,
    ScanConfig,

    # Pattern matchers
    prompt_injection_matcher,
    system_prompt_leak_matcher,

    # Guard types
    GuardAction,
    GuardCheckResult,
    PerplexityGuard,
    LengthGuard,
    MLClassifierGuard,
    PIIGuard,
    ToxicityGuard,
    PatternGuard,
    EncodingGuard,
    SemanticSimilarityGuard,
    MultiLayerDefense,
    MultiLayerResult,
    LayerResult,

    # Guard convenience functions
    perplexity_guard,
    ml_classifier_guard,
    length_guard,
    pii_guard,
    toxicity_guard,
    pattern_guard,
    encoding_guard,
    semantic_similarity_guard,
    multi_layer_defense,

    # Benchmark types
    AttackSample,
    BenignSample,
    BenchmarkSample,
    BenchmarkDataset,
    GuardMetrics,
    BenchmarkTargets,
    CompetitorReference,

    # Benchmark functions
    get_attack_samples,
    get_benign_samples,
    get_oxideshield_dataset,
    get_jailbreakbench_dataset,
    get_prompt_injection_dataset,
    get_adversarial_suffix_dataset,
    get_competitor_references,
    compare_with_competitors,

    # Scanner types
    ProbeCategory,
    Probe,
    ProbeLoader,
    ProbeEvaluation,
    Finding,
    Report,

    # Scanner functions
    load_probes,
    get_probes_by_category,
    create_report,

    # License types
    LicenseTier,
    Feature,
    LicenseInfo,
    LicenseValidator,
    LicenseException,

    # License functions
    set_license_key,
    get_license_key,
    validate_license,
    get_licensed_features,
    is_feature_licensed,
    features_for_tier,
    is_community_guard,

    # Engine types
    EngineAction,
    GuardResultSummary,
    EngineResult,
    EngineMetrics,
    EngineBuilder,
    OxideShieldEngine,

    # Engine functions
    simple_engine,
    molt_engine,

    # Attestation types
    MemoryAuditStorage,
    AuditFilter,
    AttestationSigner,
    AuditEntry,
    AuditResult,
    SignedAuditEntry,
)

__all__ = [
    # Core types
    "PatternMatcher",
    "Match",
    "Severity",
    "ScanConfig",

    # Pattern matchers
    "prompt_injection_matcher",
    "system_prompt_leak_matcher",

    # Guard types
    "GuardAction",
    "GuardCheckResult",
    "PerplexityGuard",
    "LengthGuard",
    "MLClassifierGuard",
    "PIIGuard",
    "ToxicityGuard",
    "PatternGuard",
    "EncodingGuard",
    "SemanticSimilarityGuard",
    "MultiLayerDefense",
    "MultiLayerResult",
    "LayerResult",

    # Guard convenience functions
    "perplexity_guard",
    "ml_classifier_guard",
    "length_guard",
    "pii_guard",
    "toxicity_guard",
    "pattern_guard",
    "encoding_guard",
    "semantic_similarity_guard",
    "multi_layer_defense",

    # Benchmark types
    "AttackSample",
    "BenignSample",
    "BenchmarkSample",
    "BenchmarkDataset",
    "GuardMetrics",
    "BenchmarkTargets",
    "CompetitorReference",

    # Benchmark functions
    "get_attack_samples",
    "get_benign_samples",
    "get_oxideshield_dataset",
    "get_jailbreakbench_dataset",
    "get_prompt_injection_dataset",
    "get_adversarial_suffix_dataset",
    "get_competitor_references",
    "compare_with_competitors",

    # Scanner types
    "ProbeCategory",
    "Probe",
    "ProbeLoader",
    "ProbeEvaluation",
    "Finding",
    "Report",

    # Scanner functions
    "load_probes",
    "get_probes_by_category",
    "create_report",

    # License types
    "LicenseTier",
    "Feature",
    "LicenseInfo",
    "LicenseValidator",
    "LicenseException",

    # License functions
    "set_license_key",
    "get_license_key",
    "validate_license",
    "get_licensed_features",
    "is_feature_licensed",
    "features_for_tier",
    "is_community_guard",

    # Engine types
    "EngineAction",
    "GuardResultSummary",
    "EngineResult",
    "EngineMetrics",
    "EngineBuilder",
    "OxideShieldEngine",

    # Engine functions
    "simple_engine",
    "molt_engine",

    # Attestation types
    "MemoryAuditStorage",
    "AuditFilter",
    "AttestationSigner",
    "AuditEntry",
    "AuditResult",
    "SignedAuditEntry",
]
