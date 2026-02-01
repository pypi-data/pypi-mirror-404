import typing
from typing import Literal, Self

from pydantic import BaseModel, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .types import BufferMetadataProperty, DownsamplingAlgorithm, PlotextPlotMarker

default_stat_attributes = list(
    filter(
        lambda v: v not in ("id", "header_size", "header_hash"),
        typing.get_args(BufferMetadataProperty),
    )
)


class SortingConfig(BaseModel):
    attribute: BufferMetadataProperty = "process"
    order: Literal["ASC", "DESC"] = "ASC"


class TableConfig(BaseModel):
    columns: list[BufferMetadataProperty] = [
        "process",
        "compression_time",
        "compression_frq",
        "avg_time",
        "avg_frq",
    ]
    sort: SortingConfig = SortingConfig()


class PlotConfig(BaseModel):
    marker: PlotextPlotMarker = "braille"
    displayed_datapoints: int = 1_000
    downsampling: DownsamplingAlgorithm = "lttb"


class StatConfig(BaseModel):
    attributes: list[BufferMetadataProperty] = default_stat_attributes


class MetadataCacheConfig(BaseModel):
    sync_recursive: bool = True
    persist_cache: bool = False  # Will create a `.metadata.db` file


class Config(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)

    table: TableConfig = TableConfig()
    plot: PlotConfig = PlotConfig()
    stats: StatConfig = StatConfig()
    metadata_cache: MetadataCacheConfig = MetadataCacheConfig()

    @model_validator(mode="after")
    def validate_sort_config(self) -> Self:
        if self.table.sort.attribute not in self.table.columns:
            raise LookupError(
                "The sort attribute has to be in the selected columns. "
                f"Unable to find {self.table.sort.attribute} in "
                f"{self.table.columns}"
            )
        return self
