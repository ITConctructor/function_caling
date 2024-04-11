import yaml
import json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, GenerationConfig, StoppingCriteria, StoppingCriteriaList
from peft import PeftModel, PeftConfig
import re
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from formats import FORMATS_DICT

class KeywordsStoppingCriteria(StoppingCriteria):
    def __init__(self, keywords:list, tokenizer):
        self.keywords = keywords
        self.tokenizer = tokenizer

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        result = False
        for key in self.keywords:
          text = self.tokenizer.batch_decode(input_ids)[0]
          if text.endswith(key):
            result = True
        return result

class Agent():
    def __init__(self, config):
        self.prompt_format = config["prompt_format"]
        peft_config = PeftConfig.from_pretrained(config["model_args"]["model_name"])
        model_config = {
            "pretrained_model_name_or_path":peft_config.base_model_name_or_path,
            "low_cpu_mem_usage":True,
            "torch_dtype":torch.float16,
            "device_map":"auto",
            "offload_state_dict":True,
            "quantization_config":BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
                                                    bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True)
        }
        base_model = AutoModelForCausalLM.from_pretrained(**model_config)
        self.model = PeftModel.from_pretrained(base_model, config["model_name"])
        self.tokenizer = AutoTokenizer.from_pretrained(peft_config.base_model_name_or_path)
        self.generation_config = GenerationConfig.from_pretrained(model_config["pretrained_model_name_or_path"])
        self.generation_config.max_new_tokens = 1000
        self.stopping_criteria = KeywordsStoppingCriteria([FORMATS_DICT[self.prompt_format]["tool_call_e"], "</s>"], self.tokenizer)

    def generate(self, messages):
        messages = json.loads(messages)
        prompt = FORMATS_DICT[self.prompt_format]["inference"](messages)
        
        data = self.tokenizer(prompt, return_tensors="pt")
        data = {k: v.to(self.model.device) for k, v in data.items()}
        output_ids = self.model.generate(
            **data,
            generation_config=self.generation_config,
            stopping_criteria=StoppingCriteriaList([self.stopping_criteria])
        )[0]
        output_ids = output_ids[len(data["input_ids"][0]):]
        output = self.tokenizer.decode(output_ids, skip_special_tokens=True)
        role = "assistant"
        if FORMATS_DICT[self.prompt_format]["tool_call_b"] in output:
            role == "function_call"
        return json.dumps({"role":role, "content":output}, ensure_ascii=False)

config_path = "inference.yaml"
with open(config_path, "r") as f:
    config = yaml.safe_load(f)
AGENT = Agent(config=config)

app = FastAPI()
Instrumentator().instrument(app).expose(app)

@app.get("/")
def root():
    return {
        'foo': 'bar'
    }

@app.get("/urls")
def get_all_urls():
    url_list = [{"path": route.path, "name": route.name} for route in app.routes]
    return url_list

@app.get("/health-check")
def healthcheck():
    return {
        'status': 'OK'
    }

@app.get("/answer-{messages}")
def chat(messages):
    answer = AGENT.generate(messages)
    return answer


