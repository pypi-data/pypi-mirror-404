from dataclasses import dataclass, field
from pathlib import Path
from lineage.ingest.static_loaders.sqlglot.config import SqlglotConfig
from typing import Iterable

@dataclass(slots=True)
class DbtArtifactsConfig:
    target_path: Path = Path("demo/finance_dbt_project/target")
    manifest_filename: str = "manifest.json"
    catalog_filename: str = "catalog.json"
    run_results_filename: str = "run_results.json"

    def manifest_path(self) -> Path:
        return self.target_path / self.manifest_filename

    def catalog_path(self) -> Path:
        return self.target_path / self.catalog_filename

    def run_results_path(self) -> Path:
        return self.target_path / self.run_results_filename


@dataclass(slots=True)
class LineageBuildConfig:
    artifacts: DbtArtifactsConfig = field(default_factory=DbtArtifactsConfig)
    sqlglot: SqlglotConfig = field(default_factory=SqlglotConfig)
    include_tests: bool = True
    include_macros: bool = True
    include_exposures: bool = True
    snapshot_strategy: str = "replace"
    # Use single-process mode for column lineage extraction (avoids ProcessPoolExecutor)
    # Useful when running inside another process pool or when debugging
    single_process: bool = False

    def with_artifacts_path(self, path: Path | str) -> "LineageBuildConfig":
        self.artifacts.target_path = Path(path)
        return self

    def with_single_process(self, single_process: bool = True) -> "LineageBuildConfig":
        """Enable single-process mode for column lineage extraction."""
        self.single_process = single_process
        return self





def iter_dbt_artifact_paths(config: DbtArtifactsConfig) -> Iterable[Path]:
    yield config.manifest_path()
    yield config.catalog_path()
    yield config.run_results_path()
