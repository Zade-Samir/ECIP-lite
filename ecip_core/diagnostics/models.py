from typing import List
from pydantic import BaseModel, Field


class HealthReport(BaseModel):
    """
    Standard typed diagnostics health report schema.
    """
    overall_status: str = Field(..., description="Overall health state: healthy, degraded, or unhealthy")
    warnings: List[str] = Field(default_factory=list, description="List of warnings detected")
    errors: List[str] = Field(default_factory=list, description="List of critical errors detected")
    checks_passed: List[str] = Field(default_factory=list, description="Names of checks that passed")
    checks_failed: List[str] = Field(default_factory=list, description="Names of checks that failed")
    recommendations: List[str] = Field(default_factory=list, description="Recommended repair actions")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")
