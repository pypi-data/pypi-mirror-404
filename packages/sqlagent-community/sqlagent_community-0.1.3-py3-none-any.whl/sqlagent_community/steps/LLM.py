import ollama


class ResultInterpreter:
    """Interpreta resultados do banco e gera explicações em linguagem natural."""

    def __init__(self, model: str = "llama3.1:latest"):
        self.model = model

    def _format_results(self, columns, results) -> str:
        if not results:
            return "(Nenhum dado disponível)" if columns else "(Sem colunas ou dados)"

        lines = []
        for row in results:
            try:
                line = ", ".join(f"{col}: {val}" for col, val in zip(columns, row))
            except Exception:
                line = str(row)
            lines.append(line)

        return "\n".join(lines)

    def _build_prompt(self, question: str, result_text: str, history, context) -> str:
        return f"""
Você é um assistente especialista em geociências e análise ambiental,
atuando em um bate-papo técnico-profissional.

Seu objetivo é interpretar dados ambientais e florestais e responder
de forma clara, objetiva e natural em português.

========================
CONTEXTO DOS DADOS (REFERÊNCIA INTERNA) E INSTRUÇOES
========================
{context}

========================
CONTEXTO DA CONVERSA
========================
Use o histórico abaixo apenas como referência sem repeti-lo na resposta.
{history}

========================
DADOS RETORNADOS DO BANCO
========================
{result_text}

========================
PERGUNTA DO USUÁRIO
========================
"{question}"

RESPONDA A PERGUNTA!

"""

    def interpret(self, question: str, columns, results, history, context) -> str:
        result_text = self._format_results(columns, results)

        prompt = self._build_prompt(question, result_text, history, context)

        try:
            r = ollama.generate(
                model=self.model,
                prompt=prompt
            )
            response = r.get("response", "").strip()
            return response or (
                "Os dados foram processados, mas não foi possível gerar uma explicação detalhada."
            )
        except Exception as e:
            return f"Ocorreu um erro ao gerar a resposta: {e}"
