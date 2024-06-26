from typing import List, Dict, Any
import json

SYSTEM_PROMPT = (
    "You are a helpful assistant with function-calling supported. You are provided with function signatures within <TOOLS></TOOLS> XML tags. "
    "You may call one or more functions to assist with the user query. Don't make assumptions about what values to plug into functions. "
    "Here are the available tools:\n"
    "<TOOLS>\n"
    "{tools}\n"
    "</TOOLS>\n\n"
    "For each function call, return a JSON object with the function name and arguments within <TOOL_CALL></TOOL_CALL> XML tags as follows:\n"
    "<TOOL_CALL>\n"
    "{{\"name\": <function-name>, \"arguments\": <args-dict>}}\n"
    "</TOOL_CALL>\n"
    "You will get function call result within <TOOL_RESPONSE></TOOL_RESPONSE> XML tags. "
    "Answer user query based on the result."
)

S_B, S_E = "<s>", "</s>"
INST_B, INST_E = "[INST] ", " [/INST] "
SYS_B, SYS_E = "<<SYS>>\n", "\n<</SYS>>\n\n"
TOOL_CALL_B, TOOL_CALL_E = "<TOOL_CALL>\n", "\n</TOOL_CALL>\n\n"
TOOL_RESPONSE_B, TOOL_RESPONSE_E = "<TOOL_RESPONSE>\n", "\n</TOOL_RESPONSE>\n\n"


def convert(messages: List[Dict[str, Any]], functions: List[str]) -> str:
    m_dicts_base = [json.loads(m) for m in messages]
    f_dicts_base = [json.loads(f) for f in functions]

    result = {"text":[]}
    for local_messages, local_functions in zip(m_dicts_base, f_dicts_base):
      tools = ",\n".join([json.dumps(function, indent=4, ensure_ascii=False) for function in local_functions])
      local_messages[0]["content"] = SYSTEM_PROMPT.format(tools=tools)
      
      messages_string = [S_B, INST_B]
      for message in local_messages:
          if messages_string[-1] == S_E:
              messages_string.append(S_B)
              messages_string.append(INST_B)

          if message["role"] == "system":
              messages_string.append(SYS_B)
              messages_string.append(message["content"])
              messages_string.append(SYS_E)
          elif message["role"] == "user":
              messages_string.append(message["content"])
              messages_string.append(INST_E)
          elif message["role"] == "assistant":
              messages_string.append(message["content"])
              messages_string.append(S_E)
          elif message["role"] == "function_call":
              messages_string.append(TOOL_CALL_B)
              messages_string.append(message["content"])
              messages_string.append(TOOL_CALL_E)
          elif message["role"] == "function_response":
              messages_string.append(TOOL_RESPONSE_B)
              messages_string.append(message["content"])
              messages_string.append(TOOL_RESPONSE_E)
      result["text"].append("".join(messages_string))
    
    return result
