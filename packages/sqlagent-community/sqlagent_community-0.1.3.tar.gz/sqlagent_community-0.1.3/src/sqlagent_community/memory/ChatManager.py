import os
import json
import uuid


class ChatManager:
    def __init__(self, base_path="chats"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    def create_chat(self) -> str:
        chat_id = f"chat_{uuid.uuid4().hex[:8]}"
        path = self._chat_path(chat_id)

        data = {
            "chat_id": chat_id,
            "memories": {
                "chat": {
                    "summary": "",
                    "buffer": [],
                    "buffer_token_count": 0
                },
                "sql": {
                    "summary": "",
                    "buffer": [],
                    "buffer_token_count": 0
                }
            }
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return chat_id

    def chat_exists(self, chat_id: str) -> bool:
        return os.path.exists(self._chat_path(chat_id))

    def _chat_path(self, chat_id: str) -> str:
        return os.path.join(self.base_path, f"{chat_id}.json")
