from typing import List, Dict, Any
import json
import re

SYSTEM_PROMPT = (
    "Ты - незаменимый помощник, выполняющий задачу вызова функции. Тебе предоставлены сигнатуры функций, заключенные в xml теги <TOOLS></TOOLS>Ты можешь вызывать одну или несколько функций по запросу пользователя. Не придумывай значения аргументов, если они не указаны пользователем. Вызывай одну из следующих функций: \n"
    "<TOOLS>\n"
    "{tools}\n"
    "</TOOLS>"
    """Для каждого вызова функции возвращай названия функций и аргументы в формате JSON обязательно на русском языке. Результат запиши внутри тегов <TOOL_CALL></TOOL_CALL> вот так: <TOOL_CALL> {"name": <function-name>, "arguments": <args-dict>} </TOOL_CALL> После вызова функции ты получишь результат вызова внутри тегов <TOOL_RESPONSE></TOOL_RESPONSE>.Ответь на запрос пользователя на основе результата вызова функции."""
)
MESSAGE_TEMPLATE = "{role}\n{content}\n"
START_GEN_TEMPLATE = "{}\n"
GEN_TEMPLATE = "{}\n"

S_B, S_E = " <s> ", " </s>"
TOOL_CALL_B, TOOL_CALL_E = "<TOOL_CALL>\n", "\n</TOOL_CALL>\n\n"
TOOL_RESPONSE_B, TOOL_RESPONSE_E = "<TOOL_RESPONSE>\n", "\n</TOOL_RESPONSE>\n\n"
FUNCTON_CALL_TEMPLATE = TOOL_CALL_B + "{}" + TOOL_CALL_E
RESPONSE_TEMPLATE = TOOL_RESPONSE_B + "{}" + TOOL_RESPONSE_E

SYSTEM_ROLE = "system"
USER_ROLE = "user"
BOT_ROLE = "bot"
RESPONSE_ROLE = "function_response"


def row_to_tokens(row: Dict[str, Any]) -> List[str]:
    messages = json.loads(row["conversations_ru"])
    content = {
        "messages":[],
        "functions":[]
    }
    for m in messages:
        if m["role"] == "system":
            c = m["content"].split("{")[0]
            f = re.findall(r"\{\}", m["content"])
            content["functions"] = f
            new_m = {
                "role":SYSTEM_ROLE,
                "content":c
            }
            content["messages"].append(new_m)
        elif m["role"] == "user":
            new_m = {
                "role":USER_ROLE,
                "content":m["content"]
            }
            content["messages"].append(new_m)
        elif m["role"] == "assistant":
            if m["content"] == None:
                new_m = {
                    "role":BOT_ROLE,
                    "content":FUNCTON_CALL_TEMPLATE.format(json.dumps(m["function_call"], ensure_ascii=False))
                }
                content["messages"].append(new_m)
            else:
                new_m = {
                    "role":BOT_ROLE,
                    "content":m["content"]
                }
                content["messages"].append(new_m)
        elif m['role'] == "function":
            c = {
                "name":m["name"],
                "arguments":m["content"]
            }
            new_m = {
                "role":RESPONSE_ROLE,
                "content":RESPONSE_TEMPLATE.format(json.dumps(c, ensure_ascii=False))
            }
            content["messages"].append(new_m)

    messages = json.loads(content["messages"])
    functions = json.loads(content["functions"])

    # Customize system prompt
    tools = ",\n".join([json.dumps(function, indent=4) for function in functions])
    messages[0]["content"] = SYSTEM_PROMPT.format(tools=tools)

    tokens = [S_B, messages[0]["role"], messages[0]["content"], S_E]
    for i in range(1, len(messages)):
        message = messages[i]
        local_tokens = [S_B, message["role"], message["content"], S_E]
        tokens.extend(local_tokens)

    return tokens


def create_saiga_test_prompt(row) -> Dict[str, List[str]]:
    tokens = row_to_tokens(row)

    result = {
        "text": [],
        "text_target": [],
    }

    l, r = -1, 0
    for i in range(len(tokens)):
        if tokens[i] == BOT_ROLE:
            l = i
        elif tokens[i] == S_E:
            if l == -1:
                continue
            r = i
            result["text"].append("".join(tokens[:l] + [S_B, START_GEN_TEMPLATE.format(BOT_ROLE)]))
            result["text_target"].append("".join(GEN_TEMPLATE.format(tokens[l+1:r])))

    return result


def create_saiga_prompt(row: Dict[str, str]) -> str:
    result = ""
    tokens = row_to_tokens(row)
    for i, t in enumerate(tokens):
        if t == S_E:
            message = "".join([S_B, MESSAGE_TEMPLATE.format({"role":tokens[i-2], "content":tokens[i-1]})], S_E)
            result = result + message
    return result
