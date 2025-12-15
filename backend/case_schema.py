"""Pydantic schemas for validating case metadata files."""

import json
import logging
from pathlib import Path
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class DocumentMetadata(BaseModel):
    """Schema for individual document metadata within a case."""

    filename: str
    type: str
    date: str
    description: str

    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate document type is in allowed list."""
        allowed_types = [
            'evaluation_report',
            'testimony',
            'correspondence',
            'risk_assessment',
            'civil_commitment',
        ]
        if v not in allowed_types:
            logger.warning(
                f"Document type '{v}' is not in standard types: {allowed_types}. "
                f"This is allowed but may indicate a typo."
            )
        return v


class CaseMetadata(BaseModel):
    """Schema for case metadata.json files."""

    case_id: str
    title: str
    defendant: str
    date: str
    court: str
    evaluator: str
    question: str
    summary: Optional[str] = None
    documents: List[DocumentMetadata]
    key_findings: List[str] = Field(default_factory=list)

    @field_validator('case_id')
    @classmethod
    def validate_case_id(cls, v: str) -> str:
        """Validate case_id starts with 'case_'."""
        if not v.startswith('case_'):
            raise ValueError("case_id must start with 'case_'")
        return v

    @field_validator('summary')
    @classmethod
    def warn_if_no_summary(cls, v: Optional[str]) -> Optional[str]:
        """Warn if summary is missing (important for case search)."""
        if not v or not v.strip():
            logger.warning(
                "No summary provided - this may reduce effectiveness of case search feature. "
                "Consider adding a 2-3 sentence summary."
            )
        return v

    @field_validator('key_findings')
    @classmethod
    def warn_if_no_findings(cls, v: List[str]) -> List[str]:
        """Warn if key_findings is empty (important for case discovery)."""
        if len(v) == 0:
            logger.warning(
                "No key_findings provided - this may reduce effectiveness of case discovery feature. "
                "Consider adding 3-5 key findings."
            )
        return v


def validate_case_metadata(metadata_file: Path) -> Tuple[bool, Optional[CaseMetadata], List[str]]:
    """
    Validate case metadata file.

    Args:
        metadata_file: Path to metadata.json file

    Returns:
        Tuple of (is_valid, metadata_object, error_messages)
        - is_valid: True if validation passed, False otherwise
        - metadata_object: Parsed CaseMetadata object if valid, None otherwise
        - error_messages: List of error messages (empty if valid)
    """
    errors = []

    if not metadata_file.exists():
        return False, None, ["metadata.json not found"]

    try:
        with open(metadata_file, 'r') as f:
            data = json.load(f)

        metadata = CaseMetadata(**data)
        return True, metadata, []

    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON: {str(e)}")
    except Exception as e:
        # Pydantic validation errors
        if hasattr(e, 'errors'):
            for err in e.errors():
                field = '.'.join(str(x) for x in err['loc'])
                errors.append(f"{field}: {err['msg']}")
        else:
            errors.append(f"Validation error: {str(e)}")

    return False, None, errors


def validate_case_directory(case_dir: Path, case_id: str) -> Tuple[bool, List[str]]:
    """
    Validate that a case directory is properly structured.

    Args:
        case_dir: Path to case directory
        case_id: Expected case ID

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    # Check directory exists
    if not case_dir.exists():
        errors.append(f"Case directory does not exist: {case_dir}")
        return False, errors

    if not case_dir.is_dir():
        errors.append(f"Case path is not a directory: {case_dir}")
        return False, errors

    # Check metadata.json exists
    metadata_file = case_dir / "metadata.json"
    if not metadata_file.exists():
        errors.append("metadata.json file not found in case directory")
        return False, errors

    # Validate metadata structure
    is_valid, metadata_obj, metadata_errors = validate_case_metadata(metadata_file)
    if not is_valid:
        errors.extend(metadata_errors)
        return False, errors

    # Check case_id matches directory name
    if metadata_obj.case_id != case_id:
        errors.append(
            f"case_id in metadata.json ('{metadata_obj.case_id}') does not match "
            f"directory name ('{case_id}')"
        )

    # Check that document files listed in metadata actually exist
    for doc in metadata_obj.documents:
        doc_path = case_dir / doc.filename
        if not doc_path.exists():
            logger.warning(
                f"Document file '{doc.filename}' listed in metadata but not found in directory"
            )

    # Warn about documents in directory not listed in metadata
    allowed_extensions = {'.txt', '.pdf', '.docx'}
    actual_docs = [
        f for f in case_dir.iterdir()
        if f.is_file() and f.suffix.lower() in allowed_extensions and f.name != 'metadata.json'
    ]

    listed_filenames = {doc.filename for doc in metadata_obj.documents}
    unlisted_docs = [f.name for f in actual_docs if f.name not in listed_filenames]

    if unlisted_docs:
        logger.warning(
            f"Found documents in directory not listed in metadata.json: {unlisted_docs}"
        )

    return len(errors) == 0, errors
