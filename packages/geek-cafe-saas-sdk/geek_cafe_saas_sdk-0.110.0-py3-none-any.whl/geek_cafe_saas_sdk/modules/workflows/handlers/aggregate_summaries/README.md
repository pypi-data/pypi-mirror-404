# Aggregate Summaries Handler - IaC Integration

This Lambda handler aggregates real-time execution metrics into period summaries (daily, weekly, monthly, yearly). It should be triggered by an EventBridge scheduled rule.

## Handler Details

- **Entry Point**: `geek_cafe_saas_sdk.modules.workflows.handlers.aggregate_summaries.app.lambda_handler`
- **Trigger**: EventBridge Schedule (recommended: daily at 2 AM UTC)
- **Runtime**: Python 3.11+
- **Timeout**: 5 minutes (300 seconds) recommended
- **Memory**: 256 MB minimum

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DYNAMODB_TABLE_NAME` | Yes | DynamoDB table name for metrics storage |
| `AWS_REGION` | Yes | AWS region (typically set by Lambda runtime) |

## IAM Permissions Required

The Lambda execution role needs the following DynamoDB permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:Scan",
        "dynamodb:GetItem",
        "dynamodb:PutItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:${region}:${account}:table/${table_name}",
        "arn:aws:dynamodb:${region}:${account}:table/${table_name}/index/*"
      ]
    }
  ]
}
```

## CDK Integration (cdk-factory)

### Basic Lambda Definition

```typescript
// In your CDK stack or cdk-factory configuration

const aggregateSummariesLambda = new PythonFunction(this, 'AggregateSummariesFunction', {
  functionName: `${props.stackName}-aggregate-summaries`,
  entry: 'path/to/geek-cafe-saas-sdk/src',
  index: 'geek_cafe_saas_sdk/modules/workflows/handlers/aggregate_summaries/app.py',
  handler: 'lambda_handler',
  runtime: Runtime.PYTHON_3_11,
  timeout: Duration.minutes(5),
  memorySize: 256,
  environment: {
    DYNAMODB_TABLE_NAME: props.dynamoTableName,
  },
});

// Grant DynamoDB permissions
dynamoTable.grantReadWriteData(aggregateSummariesLambda);
```

### EventBridge Schedule Rule

```typescript
// Daily at 2 AM UTC
const dailyAggregationRule = new Rule(this, 'DailyAggregationRule', {
  ruleName: `${props.stackName}-daily-metrics-aggregation`,
  description: 'Triggers daily aggregation of execution metrics summaries',
  schedule: Schedule.cron({
    minute: '0',
    hour: '2',
    day: '*',
    month: '*',
    year: '*',
  }),
  targets: [new LambdaFunction(aggregateSummariesLambda)],
});
```

### cdk-factory Configuration (if using YAML/JSON config)

```yaml
# Example cdk-factory configuration
functions:
  aggregate-summaries:
    handler: geek_cafe_saas_sdk.modules.workflows.handlers.aggregate_summaries.app.lambda_handler
    runtime: python3.11
    timeout: 300
    memory: 256
    environment:
      DYNAMODB_TABLE_NAME: ${self:custom.dynamoTableName}
    events:
      - schedule:
          name: daily-metrics-aggregation
          description: Daily aggregation of execution metrics
          rate: cron(0 2 * * ? *)
          enabled: true
```

## Aggregation Behavior

### Schedule Logic

The handler determines which periods to aggregate based on when it runs:

| Day | Periods Aggregated |
|-----|-------------------|
| Any day | Daily (previous day) |
| Monday | Daily + Weekly (previous Mon-Sun) |
| 1st of month | Daily + Monthly (previous month) |
| Jan 1st | Daily + Monthly + Yearly (previous year) |

### Idempotency

The handler is idempotent. Running it multiple times for the same period will update (not duplicate) the summary records. This is safe for:
- Retry scenarios
- Manual re-runs
- Overlapping schedules

## Testing

### Manual Invocation

You can manually invoke the Lambda to test or backfill:

```bash
# Via AWS CLI
aws lambda invoke \
  --function-name your-stack-aggregate-summaries \
  --payload '{}' \
  response.json

# Check response
cat response.json
```

### Local Testing

```python
from geek_cafe_saas_sdk.modules.workflows.handlers.aggregate_summaries.app import lambda_handler

# Mock event (EventBridge format)
event = {
    "version": "0",
    "id": "test-event-id",
    "detail-type": "Scheduled Event",
    "source": "aws.events",
    "time": "2024-01-15T02:00:00Z",
    "detail": {}
}

result = lambda_handler(event, None)
print(result)
```

## Monitoring

### CloudWatch Metrics to Monitor

- `Invocations` - Should be 1/day
- `Errors` - Should be 0
- `Duration` - Track for performance
- `ConcurrentExecutions` - Should be 1

### Recommended Alarms

```typescript
// CDK alarm example
new Alarm(this, 'AggregationErrorAlarm', {
  metric: aggregateSummariesLambda.metricErrors(),
  threshold: 1,
  evaluationPeriods: 1,
  alarmDescription: 'Metrics aggregation job failed',
});
```

## Future Enhancements

1. **Execution History Integration**: For accurate duration stats, integrate with execution history records that track start/end timestamps.

2. **Parallel Processing**: For large datasets, consider using Step Functions to parallelize by tenant.

3. **Backfill Support**: Add support for backfilling historical periods via event parameters:
   ```json
   {
     "backfill": true,
     "start_date": "2024-01-01",
     "end_date": "2024-01-31"
   }
   ```

4. **SNS Notifications**: Publish aggregation results to SNS for downstream processing or alerting.
