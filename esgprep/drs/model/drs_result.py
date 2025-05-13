"""
DrsResult model for DRS operations.
"""

from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

from esgprep.drs.model.file_input import FileInput
from esgprep.drs.model.drs_operation import DrsOperation
from esgprep.drs.model.dataset import Dataset


class DrsResult(BaseModel):
    """
    Represents the result of processing a file through the ESGDRS pipeline.
    """
    input_file: FileInput
    operations: List[DrsOperation] = Field(default_factory=list)
    success: bool = Field(False, description="Whether processing succeeded")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    dataset: Optional[Dataset] = Field(None, description="Dataset this file belongs to")

    @model_validator(mode='after')
    def check_error_success_consistency(self) -> 'DrsResult':
        """Ensure that success and error_message are consistent."""
        if self.success and self.error_message:
            # Can't be successful with an error message
            self.success = False
        return self
