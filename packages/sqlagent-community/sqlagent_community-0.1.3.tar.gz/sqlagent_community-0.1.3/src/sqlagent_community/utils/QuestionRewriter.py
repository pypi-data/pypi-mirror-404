import json
from pydantic import BaseModel
from ollama import Client

class RewriteOutput(BaseModel):
    rewritten_question: str

class QuestionRewriter:
    def __init__(self, model: str = "qwen2.5:0.5b"):
        self.client = Client()
        self.model = model

    def rewrite(self, context: str, user_input: str) -> str:
        messages = [
            {
                "role": "system", 
                "content": "Given a history conversation and a new input, rewrite the question accordingly."
            },
            {
                "role": "user", 
                "content": f"Original: {context}\nInput: {user_input}"
            }
        ]

        response = self.client.chat(
            model=self.model,
            messages=messages,
            format=RewriteOutput.model_json_schema(), 
            options={"temperature": 0} 
        )

        structured_data = json.loads(response.message.content)
        
        return structured_data["rewritten_question"]

# Exemplo de uso:
if __name__ == "__main__":
    rewriter = QuestionRewriterOllama()
    result = rewriter.rewrite("Quais são os impactos ambientais mais comuns em áreas de FED que possuem DAP médio acima de 12cm?", "e se for menor?")
    print(result)