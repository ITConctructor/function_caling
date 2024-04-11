import json

from .llama import (
    create_llama_prompt,
    create_llama_test_prompt,
    llama_format_chat,
    TOOL_CALL_B as LLAMA_TOOL_CALL_B,
    TOOL_CALL_E as LLAMA_TOOL_CALL_E,
)
from .saiga_ru import (
    create_saiga_prompt,
    create_saiga_test_prompt,
    saiga_format_chat,
    TOOL_CALL_B as SAIGA_TOOL_CALL_B,
    TOOL_CALL_E as SAIGA_TOOL_CALL_E,
)

FORMATS_DICT = {
    "raw": {
        "train": lambda row: json.dumps(row),
        "test": lambda row: json.dumps(row),
        "tool_call_b": "<TOOL_CALL>",
        "tool_call_e": "</TOOL_CALL>",
        "inference":lambda chat: "Not implemented"
    },
    "llama": {
        "train": create_llama_prompt,
        "test": create_llama_test_prompt,
        "tool_call_b": LLAMA_TOOL_CALL_B,
        "tool_call_e": LLAMA_TOOL_CALL_E,
        "inference": llama_format_chat,
    },
    "saiga_ru": {
        "train": create_saiga_prompt,
        "test": create_saiga_test_prompt,
        "tool_call_b": SAIGA_TOOL_CALL_B,
        "tool_call_e": SAIGA_TOOL_CALL_E,
        "inference":saiga_format_chat
    },
}
