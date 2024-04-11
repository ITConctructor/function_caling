import requests
import json
import re
import random

class Environment():
    def __init__(self, url):
        self.url = url
        self.functions = [
            {
                "name": "sell_item",
                "description": "Продать предмет игроку",
                "parameters": { 
                    "type": "object", 
                    "properties": { 
                        "item_name": { 
                            "type": "string", 
                            "description": "Название предмета" }, 
                        "price": { 
                            "type": "number", 
                            "description": "Цена в монетах" } }, 
                        "required": [ "item_name", "price" ] }
            },
            {
                "name": "buy_item",
                "description": "Купить предмет у игрока",
                "parameters": { 
                    "type": "object", 
                    "properties": { 
                        "item_name": { 
                            "type": "string", 
                            "description": "Название предмета" }, 
                        "price": { 
                            "type": "number", 
                            "description": "Цена в монетах" } }, 
                        "required": [ "item_name", "price" ] }
            },
            {
                "name": "get_quests",
                "description": "Получить квесты",
                "parameters": { 
                    "type": "object", 
                    "properties": { 
                        "difficulty": { 
                            "type": "string", 
                            "description": "Сложность квестов", 
                            "enum": ["easy", "medium", "hard"] } }, 
                    "required": [ "difficulty" ] }
            },
            {
                "name": "get_news",
                "description": "Получить новости",
                "parameters": { 
                    "type": "object", 
                    "properties": { 
                        "theme": { 
                            "type": "string", 
                            "description": "Тема новостей", 
                            "enum": [ "война", "королевство", "турниры" ]} }, 
                    "required": [ "theme" ] }
            }]
        
        self.state = {
            "balance":100,
            "loot":[],
        }
        self.quests = {
            "easy":[],
            "medium":[],
            "hard":[]
        }
        self.news = {
            "война":[],
            "королевство":[],
            "турниры":[],
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
    
    def sell_item(self, item_name, price):
        result = {
            "Ответ":"Недостаточно денег"
        }
        try:
            price = int(price)
            if price <= self.state["balance"]:
                self.state["loot"].append(item_name)
                self.state["balance"] -= price
                result["Ответ"] = "Успешно"
            return result
        except:
            return result

    def buy_item(self, item_name, price):
        result = {
            "Ответ":"Товар отсутствует"
        }
        try:
            price = int(price)
            if item_name in self.state["loot"]:
                self.state["loot"].remove(item_name)
                self.state["balance"] += price
                result["Ответ"] = "Успешно"
            return result
        except:
            return result
    
    def get_quests(self, difficulty):
        quests = self.quests.get(difficulty, ["Квестов нет"])
        quest = random.sample(quests)
        return {"Квест":quest}

    def get_news(self, theme):
        theme = self.news.get(theme, ["Новостей нет"])
        story = random.sample(theme)
        return {"Новости":story}
    
    def default_func(self):
        return "Не удалось получить ответ."
    

