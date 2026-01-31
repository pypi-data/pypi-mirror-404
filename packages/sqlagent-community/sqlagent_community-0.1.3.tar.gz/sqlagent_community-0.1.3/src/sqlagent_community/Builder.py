from pathlib import Path
from sqlagent_community.steps.ExcelSQL import ExcelToSQLiteImporter
from sqlagent_community.steps.EmbemdSQL import Embedding
import traceback


class SQLBuilder:
    def __init__(
        self,
        excel_dir: str,
        db_file: str,
        embed_file: str,
        embed_model: str,
        excel_extensions=("*.xlsx", "*.xls"),
        verbose: bool = True
    ):
        self.excel_dir = Path(excel_dir)
        self.db_file = db_file
        self.embed_file = embed_file
        self.embed_model = embed_model
        self.excel_extensions = excel_extensions
        self.verbose = verbose

    # ------------------- UTILITÁRIOS -------------------
    def _log(self, message: str):
        if self.verbose:
            print(f"[SQLBuilder] {message}")

    def _iter_excels(self):
        for ext in self.excel_extensions:
            yield from self.excel_dir.glob(ext)

    # ------------------- STEPS -------------------
    def _import_excel(self, excel_path: Path):
        self._log(f"Importando Excel: {excel_path.name}")
        try:
            importer = ExcelToSQLiteImporter(
                excel_file=str(excel_path),
                db_file=self.db_file,
            )
            importer.run()
            self._log(f"Importação concluída: {excel_path.name}")
        except Exception:
            self._log(f"[Erro] Falha ao importar: {excel_path.name}")
            if self.verbose:
                traceback.print_exc()

    def _generate_embeddings(self):
        self._log("Gerando embeddings para o DB")
        try:
            embedding_pipeline = Embedding(
                db_path=self.db_file,
                embed_file=self.embed_file,
                embed_model=self.embed_model,
            )
            embedding_pipeline.run()
            self._log("Embeddings gerados com sucesso")
        except Exception:
            self._log("[Erro] Falha ao gerar embeddings")
            if self.verbose:
                traceback.print_exc()

    # ------------------- BUILD -------------------
    def build(self) -> None:
        if not self.excel_dir.exists():
            raise FileNotFoundError(f"Pasta não encontrada: {self.excel_dir}")
        
        self._log(f"Iniciando build a partir da pasta: {self.excel_dir}")

        # 1) Importar todos os arquivos Excel
        excel_files = list(self._iter_excels())
        if not excel_files:
            self._log("[Aviso] Nenhum arquivo Excel encontrado")
        for excel_path in excel_files:
            self._import_excel(excel_path)

        # 2) Gerar embeddings
        self._generate_embeddings()
        self._log("Build finalizado com sucesso")
