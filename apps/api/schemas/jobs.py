"""Pydantic schemas for optimization API requests and responses."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class JobCreateRequest(BaseModel):
    target_min_bytes: int = Field(..., gt=0, description="Minimum allowable file size in bytes")
    target_max_bytes: int = Field(..., gt=0, description="Maximum allowable file size in bytes")
    format: str = Field(default="auto", description="Requested format: auto, webp, avif, jpeg, png")
    quality_mode: str = Field(default="balanced", description="fast, balanced, maximum")
    metadata_policy: str = Field(default="minimal", description="strip_all, minimal, preserve_all")
    dimension_policy: str = Field(default="joint_search", description="joint_search, preserve_dimensions")
    budget_profile: str = Field(default="balanced", description="fast, balanced, max_quality")


class JobResponse(BaseModel):
    job_id: str
    status: str
    source_filename: str
    target_min_bytes: int
    target_max_bytes: int
    stage_message: str
    created_at: float
    updated_at: float
    result: Optional[Dict[str, Any]] = None
