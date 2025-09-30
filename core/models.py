OPENAI_MODELS = {
    "gpt-5-nano":       {"context": 400_000},
    "gpt-5-mini":       {"context": 400_000},
    "gpt-5":             {"context": 400_000},
    "gpt-4o-mini": {"context": 128_000},
    "gpt-4o":      {"context": 128_000},
    "gpt-4.1-mini":{"context": 128_000},
    "gpt-4.1":     {"context": 128_000},
    "gpt-3.5-turbo":{"context": 16_000}
}

LOCAL_MODELS = {
    "gpt-oss:20b_16k":       {"context": 16_384},
    "gpt-oss:20b_32k":       {"context": 32_768}
    # "qwen3:32b":       {"context": 4_000}
}