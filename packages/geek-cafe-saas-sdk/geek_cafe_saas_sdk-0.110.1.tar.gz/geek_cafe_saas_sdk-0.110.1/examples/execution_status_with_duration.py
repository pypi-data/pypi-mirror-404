"""
Example: Execution Status with Duration Calculations

Demonstrates the enhanced execution status API with duration calculations
and step breakdowns.

Geek Cafe, LLC
MIT License. See Project Root for the license information.
"""

from datetime import datetime, UTC
from geek_cafe_saas_sdk.modules.workflows.services import WorkflowService
from geek_cafe_saas_sdk.core import SystemRequestContext


def example_execution_status_with_duration():
    """Example of getting execution status with duration information."""
    
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
    
    # Get execution status
    result = service.get_status(
        execution_id="exec-abc123",
        include_steps=True
    )
    
    if result.success:
        data = result.data
        
        print("=" * 60)
        print("EXECUTION STATUS WITH DURATION")
        print("=" * 60)
        
        # Execution info
        execution = data["execution"]
        print(f"\nExecution: {execution['name']}")
        print(f"Status: {execution['status']}")
        print(f"Progress: {execution.get('progress_percent', 0)}%")
        
        # Summary with duration
        summary = data["summary"]
        print(f"\n--- Summary ---")
        print(f"Total Steps: {summary['total_steps']}")
        print(f"Completed: {summary['completed']}")
        print(f"Running: {summary['running']}")
        print(f"Failed: {summary['failed']}")
        print(f"Pending: {summary['pending']}")
        
        # Duration information (NEW!)
        if "duration_seconds" in summary:
            print(f"\n--- Duration ---")
            print(f"Total Duration: {summary['duration_seconds']} seconds")
            print(f"Human Readable: {summary['duration_human']}")
        
        # Step breakdown (NEW!)
        if "steps" in summary:
            print(f"\n--- Step Breakdown ---")
            for step in summary["steps"]:
                status_icon = "✓" if step["status"] == "completed" else "⏳" if step["status"] == "running" else "○"
                duration = step.get("duration_human", "N/A")
                print(f"{status_icon} {step['step_type']}: {step['status']} ({duration})")
        
        print("\n" + "=" * 60)


def example_response_format():
    """Example of the enhanced response format."""
    
    example_response = {
        "execution": {
            "id": "exec-abc123",
            "name": "NCA Analysis - file-456",
            "status": "succeeded",
            "progress_percent": 100
        },
        "summary": {
            "total_steps": 5,
            "completed": 5,
            "failed": 0,
            "running": 0,
            "pending": 0,
            "progress_percent": 100,
            "status_counts": {
                "pending": 0,
                "running": 0,
                "succeeded": 5,
                "failed": 0,
                "cancelled": 0,
                "timed_out": 0
            },
            # NEW: Duration information
            "duration_seconds": 925,
            "duration_human": "0:15:25",
            # NEW: Step breakdown with durations
            "steps": [
                {
                    "step_type": "data_cleaning",
                    "status": "completed",
                    "duration_seconds": 45,
                    "duration_human": "0:00:45"
                },
                {
                    "step_type": "profile_split",
                    "status": "completed",
                    "duration_seconds": 120,
                    "duration_human": "0:02:00"
                },
                {
                    "step_type": "calculation",
                    "status": "completed",
                    "duration_seconds": 600,
                    "duration_human": "0:10:00"
                },
                {
                    "step_type": "output_generation",
                    "status": "completed",
                    "duration_seconds": 90,
                    "duration_human": "0:01:30"
                },
                {
                    "step_type": "packaging",
                    "status": "completed",
                    "duration_seconds": 70,
                    "duration_human": "0:01:10"
                }
            ]
        },
        "steps": [
            # Full step details...
        ]
    }
    
    print("\n=== Enhanced Response Format ===")
    print("The response now includes:")
    print("1. duration_seconds - Total execution duration in seconds")
    print("2. duration_human - Human-readable format (HH:MM:SS)")
    print("3. steps - Array with per-step durations and status")
    print("\nEach step includes:")
    print("  - step_type: Name of the step")
    print("  - status: Current status")
    print("  - duration_seconds: Step duration (if started)")
    print("  - duration_human: Human-readable duration (if started)")


def example_duration_calculations():
    """Example of how durations are calculated."""
    
    print("\n=== Duration Calculation Logic ===")
    print("\n1. Per-Step Duration:")
    print("   - If completed: completed_utc_ts - started_utc_ts")
    print("   - If running: current_time - started_utc_ts")
    print("   - If pending: null (not started yet)")
    
    print("\n2. Overall Duration:")
    print("   - Wall clock time from earliest step start to latest step end")
    print("   - If still running: earliest_start to current_time")
    print("   - Reflects actual elapsed time (not sum of step durations)")
    
    print("\n3. Human-Readable Format:")
    print("   - Format: HH:MM:SS")
    print("   - Examples:")
    print("     - 45 seconds → '0:00:45'")
    print("     - 2 minutes → '0:02:00'")
    print("     - 1 hour 23 minutes → '1:23:00'")
    print("     - 15 minutes 25 seconds → '0:15:25'")


if __name__ == "__main__":
    print("Execution Status with Duration - Examples")
    print("=" * 60)
    
    # Show example response format
    example_response_format()
    
    # Show duration calculation logic
    example_duration_calculations()
    
    # Note: Uncomment to run with actual service
    # example_execution_status_with_duration()
