import requests
import json
import re

class Environment():
    def __init__(self, url):
        self.url = url
        self.menu = [
            {"name":"Пиво","cost":5},
            {"name":"Рыбка","cost":10},
        ]
        self.tables = [
            {"number":1, "is_free":False},
            {"number":2, "is_free":True},
        ]

        self.functions = [
            """{ "name": "buy_item", "description": "Покупка еды или напитка из меню", "parameters": { "type": "object", "properties": { "name": { "type": "string", "description": "Название позиции из меню, которую нужно приобрести" }}, "required": [ "name" ] } }""",
            """{ "name": "book_table", "description": "Бронирование столика в таверне", "parameters": { "type": "object", "properties": { "number": { "type": "string", "description": "Номер столика, который нужно забронировать" }}, "required": [ "number" ] } }"""
        ]

        self.agent_state = {
            "balance":0
        }
        
        self.state = {
            "menu":self.menu,
            "tables":self.tables,
            "agent_state":self.agent_state
        }

        SYSTEM_PROMPT = (
            "Ты - незаменимый помощник, выполняющий задачу вызова функции. Тебе предоставлены сигнатуры функций, заключенные в xml теги <TOOLS></TOOLS>"
            "Ты можешь вызывать одну или несколько функций по запросу пользователя. Не придумывай значения аргументов, если они не указаны пользователем."
            "Вызывай одну из следующих функций:\n"
            "<TOOLS>\n"
            "{tools}\n"
            "</TOOLS>\n\n"
            "Для каждого вызова функции возвращай названия функций и аргументы в формате JSON. Результат запиши внутри тегов <TOOL_CALL></TOOL_CALL> вот так: "
            "<TOOL_CALL>\n"
            "{{\"name\": <function-name>, \"arguments\": <args-dict>}}\n"
            "</TOOL_CALL>\n"
            "После вызова функции ты получишь результат вызова внутри тегов <TOOL_RESPONSE></TOOL_RESPONSE>."
            "Ответь на запрос пользователя на основе результата вызова функции."
        )

        self.history = [{"role":"system", "content":SYSTEM_PROMPT.format(tools=self.functions)}]

    def interract(self, message: str):
        self.history.append({"role":"user", "content":message})
        messages = json.dumps(self.history, ensure_ascii=False)

        answer = requests.get(f"{self.url}/answer-{messages}").content
        answer_dict = json.loads(answer)

        self.history = self.history + answer_dict

        function_call = re.findall("<TOOL_CALL>(.*)</TOOL_CALL>", answer)
        if len(function_call) > 0:
            func_name, func_args = self.parse_function(function_call[0])
        response = getattr(self, func_name, self.default_func)(**func_args)
        response = f"<TOOL_RESPONSE>{json.dumps(response, ensure_ascii=False)}</TOOL_RESPONSE>"
        self.history = self.history.append({"role":"function_response", "content":response})
        
        messages = json.dumps(self.history, ensure_ascii=False)
        answer = requests.get(f"{self.url}/answer-{messages}").content
        answer_dict = json.loads(answer)
        self.history = self.history + answer_dict
        return answer

    def parse_function(self, function_call_string):
        try:
            fc = json.loads(function_call_string)
            name = fc["name"]
            args = fc["arguments"]
            return name, args
        except:
            return "default_func", {}

    def buy_item(self, name: str):
        is_enable = "Нет"
        cost = 0
        for i in self.menu:
            if i["name"] == name:
                is_enable = "Да"
                cost = i["cost"]
                break
        result = {
            "Есть в наличии":is_enable,
            "Стоимость":cost,
        }
        return result
    def book_table(self, number: str):
        number = int(number)
        answer = "Нет такого столика"
        for t in self.tables:
            if t["number"] == number:
                if t["is_free"] == True:
                    answer = "Успешно"
                else:
                    answer = "Столик занят"
        result = {
            "Ответ":answer
        }
        return result
    def default_func(self):
        return "Не удалось получить ответ."
    

