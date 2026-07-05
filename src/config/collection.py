from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.config.config_manager import TopicConfig, UIConfig
from src.config.searches import SearchConfig


class EvaluationSelection(BaseModel):
    """Which prompt and model to use when evaluating this collection's content."""

    # NOTE: "model_config" is a reserved attribute name on pydantic BaseModel (it's used
    # for pydantic's own ConfigDict), so the Python field is named `model_config_name`
    # while the YAML key stays `model_config` via a Field alias.
    model_config = ConfigDict(populate_by_name=True)

    prompt_config: str
    model_config_name: str = Field(alias="model_config")


class CollectionConfig(BaseModel):
    """A named, self-contained collection: topic, UI branding, evaluation, searches."""

    name: str
    topic: TopicConfig
    ui: UIConfig
    evaluation: EvaluationSelection
    searches: SearchConfig
    default_search: str

    @property
    def stages_base(self) -> Path:
        return Path("stages") / self.name

    @property
    def output_base(self) -> Path:
        return Path("output") / self.name

    @model_validator(mode="after")
    def validate_default_search(self) -> "CollectionConfig":
        search = self.searches.get_search(self.default_search)
        if search is None:
            raise ValueError(
                f"default_search '{self.default_search}' is not defined in searches"
            )
        if not search.enabled:
            raise ValueError(f"default_search '{self.default_search}' is not enabled")
        return self


def load_collection(name: str, config_dir: str | Path = "config") -> CollectionConfig:
    """Load a CollectionConfig from config_dir/collections/<name>.yaml."""
    config_path = Path(config_dir) / "collections" / f"{name}.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Unknown collection '{name}': {config_path} not found")

    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise TypeError(f"Collection configuration must be a YAML object: {config_path}")

    return CollectionConfig.model_validate(data)
