#!/usr/bin/env python3
"""
Cleanup stale workflow metrics by comparing actual running executions vs metrics counters.

This script:
1. Queries all workflow metrics records
2. For each user, counts actual running executions
3. Compares actual count vs metrics.active_count
4. Resets metrics to match reality

Run this after deploying the WorkflowService fix to clean up accumulated stale metrics.

Usage:
    python cleanup_stale_metrics.py \
      --table-name <table> \
      --tenant-id <tenant> \
      --metric-type <type> \
      [--profile <aws-profile>] \
      [--live]

Examples:
    # Dry run with default AWS credentials
    python cleanup_stale_metrics.py \
      --table-name my-table \
      --tenant-id tenant-123 \
      --metric-type nca_analysis

    # Live update with specific AWS profile
    python cleanup_stale_metrics.py \
      --table-name my-table \
      --tenant-id tenant-123 \
      --metric-type workflow \
      --profile production \
      --live
"""

import argparse
import os
from typing import Dict, List
from boto3_assist.dynamodb.dynamodb import DynamoDB
from geek_cafe_saas_sdk.core.request_context import SystemRequestContext
from geek_cafe_saas_sdk.modules.workflows.models.execution import Workflow, WorkflowStatus
from geek_cafe_saas_sdk.modules.workflows.models.workflow_metrics import WorkflowMetrics


def get_actual_running_counts(
    dynamodb: DynamoDB,
    table_name: str,
    tenant_id: str,
    metric_type: str
) -> Dict[str, int]:
    """
    Get actual count of running executions per user.
    
    Returns:
        Dict mapping user_id -> count of running executions
    """
    print(f"\nQuerying actual running executions for tenant {tenant_id}...")
    
    # Query all executions for tenant
    query_model = Workflow()
    query_model.tenant_id = tenant_id
    query_model.execution_type = metric_type
    
    # Use GSI to query by tenant + execution_type
    from boto3.dynamodb.conditions import Key
    
    response = dynamodb.query(
        table_name=table_name,
        index_name="gsi1",
        key_condition_expression=Key("gsi1_pk").eq(f"TENANT#{tenant_id}#TYPE#{metric_type}"),
    )
    
    items = response.get("Items", [])
    print(f"Found {len(items)} total executions")
    
    # Count running executions per user
    running_counts = {}
    for item in items:
        execution = Workflow().map(item)
        
        # Only count root executions (not children)
        if execution.parent_id:
            continue
        
        # Only count running executions
        if execution.status == WorkflowStatus.RUNNING:
            user_id = execution.user_id
            running_counts[user_id] = running_counts.get(user_id, 0) + 1
    
    print(f"Found {sum(running_counts.values())} running root executions across {len(running_counts)} users")
    return running_counts


def get_metrics_records(
    dynamodb: DynamoDB,
    table_name: str,
    tenant_id: str,
    metric_type: str
) -> List[WorkflowMetrics]:
    """Get all metrics records for tenant."""
    print(f"\nQuerying metrics records for tenant {tenant_id}...")
    
    query_model = WorkflowMetrics()
    query_model.tenant_id = tenant_id
    query_model.metric_type = metric_type
    
    # Use GSI2 to query by tenant + metric_type
    from boto3.dynamodb.conditions import Key
    
    response = dynamodb.query(
        table_name=table_name,
        index_name="gsi2",
        key_condition_expression=Key("gsi2_pk").eq(f"TENANT#{tenant_id}#METRIC#{metric_type}"),
    )
    
    items = response.get("Items", [])
    metrics_list = [WorkflowMetrics().map(item) for item in items]
    
    print(f"Found {len(metrics_list)} metrics records")
    return metrics_list


def cleanup_metrics(
    dynamodb: DynamoDB,
    table_name: str,
    tenant_id: str,
    metric_type: str,
    dry_run: bool = True
):
    """
    Cleanup stale metrics by resetting to actual running counts.
    
    Args:
        dynamodb: DynamoDB instance
        table_name: Table name
        tenant_id: Tenant ID to clean up
        metric_type: Metric type
        dry_run: If True, only report issues without fixing
    """
    print(f"\n{'=' * 80}")
    print(f"Cleaning up metrics for tenant: {tenant_id}")
    print(f"Metric type: {metric_type}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE UPDATE'}")
    print(f"{'=' * 80}")
    
    # Get actual running counts
    actual_counts = get_actual_running_counts(dynamodb, table_name, tenant_id, metric_type)
    
    # Get metrics records
    metrics_list = get_metrics_records(dynamodb, table_name, tenant_id, metric_type)
    
    # Compare and fix
    print(f"\n{'=' * 80}")
    print("COMPARISON RESULTS")
    print(f"{'=' * 80}")
    
    fixes_needed = []
    
    for metrics in metrics_list:
        user_id = metrics.owner_id
        
        # Skip tenant-wide metrics for now
        if user_id == WorkflowMetrics.TENANT_WIDE_OWNER:
            continue
        
        actual_count = actual_counts.get(user_id, 0)
        metrics_count = metrics.active_count
        
        if actual_count != metrics_count:
            diff = metrics_count - actual_count
            fixes_needed.append({
                "user_id": user_id,
                "metrics_count": metrics_count,
                "actual_count": actual_count,
                "diff": diff,
                "metrics": metrics,
            })
            
            print(f"\n❌ MISMATCH - User: {user_id}")
            print(f"   Metrics says: {metrics_count} running")
            print(f"   Actually:     {actual_count} running")
            print(f"   Difference:   {diff} (stale)")
        else:
            print(f"\n✅ OK - User: {user_id} ({actual_count} running)")
    
    # Apply fixes
    if fixes_needed:
        print(f"\n{'=' * 80}")
        print(f"FIXES NEEDED: {len(fixes_needed)} users")
        print(f"{'=' * 80}")
        
        if dry_run:
            print("\n⚠️  DRY RUN MODE - No changes will be made")
            print("Run with --live to apply fixes")
        else:
            print("\n🔧 Applying fixes...")
            
            for fix in fixes_needed:
                metrics = fix["metrics"]
                user_id = fix["user_id"]
                old_count = fix["metrics_count"]
                new_count = fix["actual_count"]
                
                print(f"\nFixing user {user_id}: {old_count} -> {new_count}")
                
                # Update metrics
                metrics.active_count = new_count
                metrics.prep_for_save()
                
                # Save to DynamoDB
                item = metrics.to_dict()
                dynamodb.save(table_name=table_name, item=item)
                
                print(f"  ✅ Updated")
            
            print(f"\n✅ All fixes applied!")
    else:
        print(f"\n✅ No fixes needed - all metrics are accurate!")
    
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    print(f"Total users checked: {len(metrics_list)}")
    print(f"Users with stale metrics: {len(fixes_needed)}")
    print(f"Total stale count: {sum(f['diff'] for f in fixes_needed)}")
    print(f"{'=' * 80}\n")


def main():
    parser = argparse.ArgumentParser(description="Cleanup stale workflow metrics")
    parser.add_argument("--profile", help="AWS profile name to use for credentials")
    parser.add_argument("--table-name", required=True, help="DynamoDB table name")
    parser.add_argument("--tenant-id", required=True, help="Tenant ID to clean up")
    parser.add_argument("--metric-type", required=True, help="Metric type (e.g., 'nca_analysis', 'workflow')")
    parser.add_argument("--live", action="store_true", help="Apply fixes (default is dry-run)")
    
    args = parser.parse_args()
    
    # Create DynamoDB instance with optional profile
    if args.profile:
        dynamodb = DynamoDB(aws_profile=args.profile)
    else:
        dynamodb = DynamoDB()
    
    # Run cleanup
    cleanup_metrics(
        dynamodb=dynamodb,
        table_name=args.table_name,
        tenant_id=args.tenant_id,
        metric_type=args.metric_type,
        dry_run=not args.live,
    )


if __name__ == "__main__":
    main()
