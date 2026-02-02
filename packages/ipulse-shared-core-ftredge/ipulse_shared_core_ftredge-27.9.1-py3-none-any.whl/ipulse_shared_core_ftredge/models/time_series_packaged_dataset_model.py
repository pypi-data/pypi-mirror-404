# pylint: disable=missing-module-docstring, missing-class-docstring
from typing import List, Optional, TypeVar, Generic, ClassVar
from datetime import datetime
from pydantic import Field, BaseModel
from ipulse_shared_core_ftredge.models.base_nosql_model import BaseNoSQLModel

# Generic type for the records within the dataset
RecordsSamplingType = TypeVar('RecordsSamplingType', bound=BaseModel)

class TimeSeriesPackagedDatasetModel(BaseNoSQLModel, Generic[RecordsSamplingType]):
    """
    An intermediary model for time series datasets that holds aggregated records.
    It provides a generic way to handle different types of time series records.
    """
    SCHEMA_ID: ClassVar[str] = ""
    SCHEMA_NAME: ClassVar[str] = ""
    VERSION: ClassVar[int] = 1


    subject_id: str = Field(default="", description="The unique identifier for the subject.")
    subject_category: str = Field(default="", description="The subject category eg. EQUITY, DERIVATIVE, CRYPTO etc.")

    # Generic lists for different temporal buckets of records
    max_bulk_records: List[RecordsSamplingType] = Field(default_factory=list)
    latest_bulk_records: Optional[List[RecordsSamplingType]] = Field(default_factory=list)
    latest_intraday_records: Optional[List[RecordsSamplingType]] = Field(default_factory=list)

    # Metadata fields
    max_bulk_updated_at: Optional[datetime] = None
    max_bulk_updated_by: Optional[str] = None
    max_bulk_recent_date_id: Optional[datetime] = None
    max_bulk_oldest_date_id: Optional[datetime] = None
    latest_bulk_recent_date_id: Optional[datetime] = None
    latest_bulk_oldest_date_id: Optional[datetime] = None
    latest_record_updated_at: Optional[datetime] = None
    latest_record_updated_by: Optional[str] = None
    latest_record_change_id: Optional[str] = None
    latest_intraday_bulk_updated_at: Optional[datetime] = None
    latest_intraday_bulk_updated_by: Optional[str] = None

    @property
    def id(self) -> str:
        """Return subject_id for backward compatibility and consistency."""
        return self.subject_id
