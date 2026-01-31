"""
Example: Workflow Date Range Queries

Demonstrates how to query workflows with date range filtering.
All date/time parameters accept timezone-aware or naive datetime objects.
Naive datetimes are assumed to be UTC.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from datetime import datetime, UTC, timedelta
from zoneinfo import ZoneInfo

from geek_cafe_saas_sdk.modules.workflows.services import WorkflowService
from geek_cafe_saas_sdk.core import SystemRequestContext


def example_date_range_queries():
    """Examples of querying workflows with date ranges."""
    
    # Setup (assumes you have a WorkflowService instance)
    context = SystemRequestContext(
        tenant_id="tenant_123",
        user_id="user_456",
        source="example"
    )
    service = WorkflowService(
        dynamodb=dynamodb,  # Your DynamoDB instance
        table_name="workflows",
        request_context=context
    )
    
    # =========================================================================
    # Example 1: Running executions from last 24 hours
    # =========================================================================
    start = datetime.now(UTC) - timedelta(hours=24)
    result = service.list_by_status(
        status="running",
        start_date=start
    )
    print(f"Running executions (last 24h): {len(result.data)}")
    
    # =========================================================================
    # Example 2: Failed executions in a specific date range
    # =========================================================================
    result = service.list_by_status(
        status="failed",
        start_date=datetime(2024, 1, 1, tzinfo=UTC),
        end_date=datetime(2024, 1, 31, 23, 59, 59, tzinfo=UTC)
    )
    print(f"Failed executions in January 2024: {len(result.data)}")
    
    # =========================================================================
    # Example 3: NCA analyses from last week
    # =========================================================================
    start = datetime.now(UTC) - timedelta(days=7)
    result = service.list_by_execution_type(
        execution_type="nca_analysis",
        start_date=start
    )
    print(f"NCA analyses (last 7 days): {len(result.data)}")
    
    # =========================================================================
    # Example 4: Running calculations from today
    # =========================================================================
    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    result = service.list_by_execution_type(
        execution_type="calculation",
        status="running",
        start_date=today_start
    )
    print(f"Running calculations today: {len(result.data)}")
    
    # =========================================================================
    # Example 5: Using different timezones (automatically converted to UTC)
    # =========================================================================
    # Query for executions that started between 9 AM and 5 PM EST on Jan 15, 2024
    est = ZoneInfo("America/New_York")
    start = datetime(2024, 1, 15, 9, 0, tzinfo=est)   # 9 AM EST
    end = datetime(2024, 1, 15, 17, 0, tzinfo=est)    # 5 PM EST
    
    result = service.list_by_execution_type(
        execution_type="nca_analysis",
        start_date=start,  # Automatically converted to UTC
        end_date=end       # Automatically converted to UTC
    )
    print(f"Executions during business hours (EST): {len(result.data)}")
    
    # =========================================================================
    # Example 6: Naive datetime (assumed UTC)
    # =========================================================================
    # If you don't specify timezone, it's assumed to be UTC
    start = datetime(2024, 1, 1, 0, 0, 0)  # Assumed UTC
    end = datetime(2024, 1, 31, 23, 59, 59)  # Assumed UTC
    
    result = service.list_by_status(
        status="succeeded",
        start_date=start,
        end_date=end
    )
    print(f"Successful executions in January (UTC): {len(result.data)}")
    
    # =========================================================================
    # Example 7: Open-ended ranges
    # =========================================================================
    # Only start_date (all executions after this date)
    start = datetime(2024, 1, 1, tzinfo=UTC)
    result = service.list_by_status(
        status="running",
        start_date=start
        # No end_date = no upper limit
    )
    print(f"Running executions since Jan 1, 2024: {len(result.data)}")
    
    # Note: For open-ended ranges, the query uses begins_with instead of between
    # This is less efficient, so prefer specifying both start and end dates


def example_timestamp_conversion():
    """Examples of datetime to UTC timestamp conversion."""
    
    # The service handles all conversions internally, but you can use the
    # helper method directly if needed
    
    # UTC datetime
    dt = datetime(2024, 1, 31, 12, 0, tzinfo=UTC)
    ts = WorkflowService._datetime_to_utc_timestamp(dt)
    print(f"UTC datetime: {dt} -> {ts}")
    
    # EST datetime (converted to UTC)
    est = ZoneInfo("America/New_York")
    dt = datetime(2024, 1, 31, 7, 0, tzinfo=est)  # 7 AM EST = 12 PM UTC
    ts = WorkflowService._datetime_to_utc_timestamp(dt)
    print(f"EST datetime: {dt} -> {ts} (same as above)")
    
    # Naive datetime (assumed UTC)
    dt = datetime(2024, 1, 31, 12, 0)
    ts = WorkflowService._datetime_to_utc_timestamp(dt)
    print(f"Naive datetime: {dt} -> {ts} (assumed UTC)")


if __name__ == "__main__":
    example_date_range_queries()
    example_timestamp_conversion()
