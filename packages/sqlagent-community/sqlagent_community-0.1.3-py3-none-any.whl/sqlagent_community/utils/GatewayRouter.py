import json
from pydantic import BaseModel
from typing import Literal
from ollama import Client

class RouterOutput(BaseModel):
    action: Literal["REWRITE", "VANILLA"]

class GatewayRouter:
    def __init__(self, model: str = "llama3.1"):
        # Inicializa o cliente do Ollama
        self.client = Client()
        self.model = model

    def route(self, user_input: str, context: str | None) -> RouterOutput:
        system_prompt = """
    Você é um orquestrador de contexto. Sua única missão é determinar a independência semântica da NOVA PERGUNTA.

    CRITÉRIOS DE DECISÃO:

    1. VANILLA: A NOVA PERGUNTA é compreensível por um estranho que não ouviu o HISTÓRICO. 
    - Se ela cita a entidades e critérios completos, ela é independente. 
    - é uma saudação, agradecimento ou algo geral sem foco.
    - Mesmo que o tema seja o mesmo do histórico, se ela não usa termos de ligação (ex: "e estes?", "desses", "daqueles"), é VANILLA.

    2. REWRITE: A NOVA PERGUNTA é um fragmento ou depende de referência anterior.
    - Exemplos: "E os menores?", "Qual o impacto deles?", "Filtre por 10 então", "Mostre mais".
    - Sem o HISTÓRICO, a pergunta se torna impossível de converter em SQL.

    Responda apenas JSON: {"action": "VANILLA" | "REWRITE"}
    """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"### HISTÓRICO DAS MENSAGENS ANTERIORES:\n{context}\n\n### NOVA PERGUNTA DO USUÁRIO (AVALIE ESTA):\n{user_input}"}
        ]

        response = self.client.chat(
            model=self.model,
            messages=messages,
            format=RouterOutput.model_json_schema(),
            options={"temperature": 0.0} 
        )
        output_data = json.loads(response.message.content)
        
        return RouterOutput.model_validate(output_data)

if __name__ == "__main__":
    router = GatewayRouterOllama()
    decisao = router.route("e apenas se for igual?", "Quais são os impactos ambientais mais comuns em áreas de FED que possuem DAP médio acima de 12cm?")
    print(decisao.action)