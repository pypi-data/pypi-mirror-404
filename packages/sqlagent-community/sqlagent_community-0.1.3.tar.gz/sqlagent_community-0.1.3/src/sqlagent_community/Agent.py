from sqlagent_community.steps.GenerateSQL import SQLGenerator
from sqlagent_community.steps.ExecuteSQL import SQLiteExecutor
from sqlagent_community.steps.LLM import ResultInterpreter
from sqlagent_community.steps.Search import SemanticSearch
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.markdown import Markdown
import traceback


class SQLAgent:
    def __init__(
        self,
        db_path: str,
        embed_file: str,
        embedding_model,
        llm_model: str,
        text2sql: str,
        memory=None,
        context: str | None = None,
        verbose: bool = True
    ):
        self.verbose = verbose
        self.console = Console()
        self.memory = memory
        self.context_path = context

        # Componentes do pipeline
        self.searcher = SemanticSearch(embed_file, embedding_model)
        self.sql_generator = SQLGenerator(text2sql)
        self.executor = SQLiteExecutor(db_path)
        self.interpreter = ResultInterpreter(model=llm_model)

    # ------------------- UTILITÁRIOS -------------------
    def _step(self, title: str):
        if self.verbose:
            self.console.print(f"\n[bold cyan]▶ {title}[/bold cyan]")

    def _code_block(self, code: str, lang="sql"):
        if self.verbose:
            syntax = Syntax(code, lang, theme="monokai", line_numbers=False)
            self.console.print(syntax)

    def _panel(self, content: str, title: str = "", style="white"):
        if self.verbose:
            self.console.print(Panel(content, title=title, style=style))

    # ------------------- MEMÓRIA -------------------
    def _load_memory(self, key: str) -> str:
        if not self.memory:
            return ""
        try:
            memory_vars = self.memory.load_memory_variables()
            return memory_vars.get(key, "")
        except Exception:
            if self.verbose:
                self.console.print("[red]Erro ao carregar memória[/red]")
                traceback.print_exc()
            return ""

    def _load_chat(self) -> str:
        return self._load_memory("chat")

    def _load_sql_history(self) -> str:
        return self._load_memory("sql")

    # ------------------- CONTEXTO -------------------
    def _load_context(self) -> str:
        if not self.context_path:
            return ""
        path = Path(self.context_path)
        if not path.exists() or not path.is_file():
            if self.verbose:
                self.console.print(f"[yellow]Context file not found: {self.context_path}[/yellow]")
            return ""
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            if self.verbose:
                self.console.print(f"[red]Erro ao ler arquivo de contexto[/red]")
                traceback.print_exc()
            return ""

    # ------------------- PIPELINE -------------------
    def _semantic_search(self, query: str) -> list:
        try:
            result = self.searcher.search(query)
            self._panel(str(result), title="Schema Context", style="green")
            return result
        except Exception:
            if self.verbose:
                self.console.print("[red]Erro na busca semântica[/red]")
                traceback.print_exc()
            return []

    def _generate_sql(self, query: str, schema: list, sql_history: str | None) -> str:
        try:
            sql_query = self.sql_generator.generate(query, schema, sql_history)
            self._code_block(sql_query, "sql")
            return sql_query
        except Exception:
            if self.verbose:
                self.console.print("[red]Erro na geração de SQL[/red]")
                traceback.print_exc()
            return ""

    def _execute_sql(self, sql_query: str):
        try:
            columns, results = self.executor.execute(sql_query)
            if self.verbose:
                table = Table(show_header=True, header_style="bold magenta")
                for col in columns:
                    table.add_column(col)
                for row in results[:10]:  # limitar visualização
                    table.add_row(*map(str, row))
                self.console.print(table)
            return columns, results
        except Exception:
            if self.verbose:
                self.console.print("[red]Erro na execução do SQL[/red]")
                traceback.print_exc()
            return [], []

    def _interpret_results(self, query: str, columns: list, results: list, chat_history: str, context: str) -> str:
        try:
            answer = self.interpreter.interpret(query, columns, results, chat_history, context)
            self._panel(answer, title="Final Answer", style="bold yellow")
            return answer
        except Exception:
            if self.verbose:
                self.console.print("[red]Erro na interpretação do LLM[/red]")
                traceback.print_exc()
            return "Erro na interpretação dos resultados."

    # ------------------- EXECUÇÃO -------------------
    def run(self, user_input: str) -> dict:
        self._step("User Question")
        self._panel(user_input, style="white")

        chat_history = self._load_chat()
        sql_history = None
        context = self._load_context()

        # Semantic Search
        self._step("Semantic Search")
        schema = self._semantic_search(user_input)
        if len(schema) == 0:
            sql_history = self._load_sql_history()

        # SQL Generation
        self._step("SQL Generation")
        sql_query = self._generate_sql(user_input, schema, sql_history)

        # SQL Execution
        self._step("SQL Execution")
        columns, results = self._execute_sql(sql_query)

        # LLM Interpretation
        self._step("LLM Interpretation")
        answer = self._interpret_results(user_input, columns, results, chat_history, context)

        # Save Memory
        if self.memory:
            try:
                self.memory.save_context("chat", {"input": user_input}, {"output": answer})
                self.memory.save_context("sql", {"input": user_input}, {"output": sql_query})
            except Exception:
                if self.verbose:
                    self.console.print("[red]Erro ao salvar memória[/red]")
                    traceback.print_exc()

        return {
            "answer": answer,
            "sql_query": sql_query,
            "sql_columns": columns,
            "sql_results": results
        }
