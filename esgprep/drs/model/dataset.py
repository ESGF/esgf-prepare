"""
Dataset model for DRS operations.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from esgprep.drs.model.dataset_version import DatasetVersion


class Dataset(BaseModel):
    """
    Represents a dataset with multiple versions in the DRS structure.
    """
    dataset_id: str = Field(..., description="Dataset identifier")
    versions: List[DatasetVersion] = Field(default_factory=list, description="Dataset versions")
    facets: Dict[str, str] = Field(default_factory=dict, description="DRS facets for this dataset")

    @property
    def latest_version(self) -> Optional[DatasetVersion]:
        """Get the latest version of the dataset."""
        if not self.versions:
            return None
        return sorted(self.versions, key=lambda v: v.version_id, reverse=True)[0]
