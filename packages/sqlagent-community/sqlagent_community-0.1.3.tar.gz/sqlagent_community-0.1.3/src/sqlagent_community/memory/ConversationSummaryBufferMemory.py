import os
import json
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ConversationSummaryBufferMemory:
    chat_id: str
    storage_path: str = "chats"
    max_token_limit: int = 200

    memories: Dict[str, Dict] = field(default_factory=dict)

    def __post_init__(self):
        self.file_path = os.path.join(self.storage_path, f"{self.chat_id}.json")

        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Chat {self.chat_id} not found")

        self._load()

        self.model_name = "t5-small"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)

    # -------- PUBLIC API --------

    def save_context(
        self,
        memory_type: str,  # "chat" | "sql"
        inputs: Dict[str, str],
        outputs: Dict[str, str]
    ):
        self._ensure_memory(memory_type)

        self._add_message(memory_type, f"User: {inputs['input']}")
        self._add_message(memory_type, f"Assistant: {outputs['output']}")

        if self.memories[memory_type]["buffer_token_count"] > self.max_token_limit:
            self._summarize_buffer(memory_type)

        self._persist()

    def load_memory_variables(self) -> Dict[str, str]:
        result = {}

        for memory_type, data in self.memories.items():
            text = ""

            if data["summary"]:
                text += f"Conversation summary:\n{data['summary']}\n\n"

            if data["buffer"]:
                text += "Recent conversation:\n"
                text += "\n".join(data["buffer"])

            result[memory_type] = text.strip()

        return result

    # -------- INTERNALS --------

    def _ensure_memory(self, memory_type: str):
        if memory_type not in self.memories:
            self.memories[memory_type] = {
                "summary": "",
                "buffer": [],
                "buffer_token_count": 0
            }

    def _add_message(self, memory_type: str, message: str):
        mem = self.memories[memory_type]
        mem["buffer"].append(message)
        mem["buffer_token_count"] += self._count_tokens(message)

    def _summarize_buffer(self, memory_type: str):
        mem = self.memories[memory_type]

        text = ""
        if mem["summary"]:
            text += f"Existing summary:\n{mem['summary']}\n\n"

        text += "New conversation:\n"
        text += "\n".join(mem["buffer"])

        mem["summary"] = self._run_summarizer(text)
        mem["buffer"] = []
        mem["buffer_token_count"] = 0

    def _run_summarizer(self, text: str) -> str:
        prompt = "summarize: " + text

        input_ids = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=1024
        ).input_ids

        outputs = self.model.generate(
            input_ids,
            max_length=200,
            min_length=50,
            do_sample=False
        )

        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

    def _count_tokens(self, text: str) -> int:
        return len(self.tokenizer.encode(text))

    def _load(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.memories = data.get("memories", {})

    def _persist(self):
        data = {
            "chat_id": self.chat_id,
            "memories": self.memories
        }

        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
