"""
Demo script to verify the Centralized Observability & Logging Framework.
Shows correlation IDs, timing execution logs, and safe exception logs.
"""
import logging
from ecip_core.logging import (
    get_logger,
    CorrelationIdContext,
    measure_time,
    log_duration,
)

logger = get_logger("demo_module")

@log_duration("Finished calculations in math_helper", logger)
def perform_calculations():
    # Simulate work
    total = sum(i * i for i in range(10000))
    return total

print("\n" + "="*70)
print("     ECIP Lite — Observability & Logging Framework Demo")
print("="*70)

# Scenario 1: Standard structured logging
print("1. Standard Log Message (No Correlation ID context yet):")
logger.info("This is a simple informational message from the app.")
print("-" * 70)

# Scenario 2: Logging inside a correlation context
print("2. Log Message with request correlation ID:")
with CorrelationIdContext("request-uuid-abc-123") as cid:
    logger.info(f"Binding request context with CID: {cid}")
    logger.warning("Resource utilization warning detected.")
    
    # Run helper function with log duration decorator
    perform_calculations()
print("-" * 70)

# Scenario 3: Execution timing measurement
print("3. Performance Execution Timing measurement using Context Manager:")
with CorrelationIdContext("timing-uuid-xyz-789"):
    with measure_time("Expensive search operation executed", logger, logging.INFO):
        # Simulate work
        _ = [x for x in range(100000) if x % 3 == 0]
print("-" * 70)

# Scenario 4: Safe Exception handling
print("4. Safe exception logging (Prevent crash during error tracing):")
try:
    _ = 1 / 0
except ZeroDivisionError as e:
    logger.exception_safe("Failed to divide values in division operation", e)

print("=" * 70)
print("Demo complete! All structured logs formatted successfully.")
print("=" * 70 + "\n")
