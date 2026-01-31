import ollama
from sqlagent_community.utils.BuildPromptSQL import build_prompt
import re


class SQLGenerator:
    """Gera consultas SQL a partir de perguntas em linguagem natural."""

    def __init__(
        self,
        model: str = "qwen2.5-coder:7b",
        temperature: float = 0.0,
        top_p: float = 0.9,
        repeat_penalty: float = 1.1,
        num_ctx: int = 8152,
    ):
        self.model = model
        self.options = {
            "temperature": temperature,
            "top_p": top_p,
            "repeat_penalty": repeat_penalty,
            "num_ctx": num_ctx,
        }

    def _clean_sql_response(self, response: str) -> str:
        """Remove blocos de markdown e espaços extras da resposta."""
        match = re.search(r"```(?:sql)?\s*(.*?)\s*```", response, re.DOTALL | re.IGNORECASE)
        
        if match:
            sql = match.group(1)
        else:
            sql = response

        return sql.strip()

    def _build_prompt(self, question: str, schema, context) -> str:
        return build_prompt(question, schema, context)

    def generate(self, question: str, schema, context) -> str:
        prompt = self._build_prompt(question, schema, context)

        r = ollama.generate(
            model=self.model,
            prompt=prompt,
            options=self.options,
        )

        raw_response = r.get("response", "").strip()
        
        return self._clean_sql_response(raw_response)
        

