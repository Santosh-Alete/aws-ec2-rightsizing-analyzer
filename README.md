# AWS EC2 Rightsizing Analyzer

Enterprise-scale EC2 rightsizing tool that analyzes CloudWatch metrics across 100+ AWS accounts using cross-account IAM roles, generates cost-saving recommendations, and runs automatically on ECS Fargate via scheduled tasks.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Management Account                       │
│  ┌────────────────────────────────────────────────────┐    │
│  │  ECS Fargate Task (Scheduled via EventBridge)      │    │
│  │  - Assumes cross-account roles                     │    │
│  │  - Fetches CloudWatch metrics                      │    │
│  │  - Queries Cost Explorer                           │    │
│  │  - Generates recommendations                       │    │
│  └────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │  S3 Bucket (Reports Storage)                       │    │
│  │  - Daily CSV reports                               │    │
│  │  - Historical data                                 │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ AssumeRole
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Target Accounts (100+)                          │
│  ┌────────────────────────────────────────────────────┐    │
│  │  IAM Role: EC2RightsizingAnalyzerRole             │    │
│  │  - Read CloudWatch metrics                         │    │
│  │  - List EC2 instances                              │    │
│  │  - Read tags                                       │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Features

- **Multi-Account Support**: Analyze 100+ AWS accounts using cross-account IAM roles
- **CloudWatch Integration**: Pull CPU, memory, network, and disk metrics
- **Cost Explorer Integration**: Get actual EC2 costs and pricing data
- **Rightsizing Recommendations**: Suggest optimal instance types based on utilization
- **Automated Scheduling**: Run daily via ECS Fargate scheduled tasks
- **S3 Report Storage**: Store daily reports with historical tracking
- **Terraform Deployment**: Complete IaC for all AWS resources
- **Tag-Based Analysis**: Group recommendations by team/environment
- **Savings Estimation**: Calculate potential monthly/annual savings

## Project Structure

```
.
├── src/
│   ├── analyzer.py           # Main analysis logic
│   ├── aws_client.py          # AWS SDK wrapper with cross-account
│   ├── metrics_collector.py   # CloudWatch metrics collection
│   ├── cost_calculator.py     # Cost analysis and savings
│   └── report_generator.py    # CSV/JSON report generation
├── terraform/
│   ├── main.tf               # Main Terraform config
│   ├── ecs.tf                # ECS cluster and task definition
│   ├── iam.tf                # IAM roles and policies
│   ├── eventbridge.tf        # Scheduled task trigger
│   ├── s3.tf                 # S3 bucket for reports
│   └── variables.tf          # Terraform variables
├── config/
│   └── accounts.yaml         # List of AWS accounts to analyze
├── Dockerfile                # Container image
├── requirements.txt          # Python dependencies
└── README.md
```

## Prerequisites

- AWS CLI configured with management account credentials
- Terraform >= 1.0
- Docker (for local testing)
- Python 3.11+

## Quick Start

### 1. Configure Accounts

Edit `config/accounts.yaml`:

```yaml
accounts:
  - account_id: "123456789012"
    name: "Production"
    role_name: "EC2RightsizingAnalyzerRole"
    regions:
      - us-east-1
      - us-west-2
  
  - account_id: "987654321098"
    name: "Development"
    role_name: "EC2RightsizingAnalyzerRole"
    regions:
      - us-east-1
```

### 2. Deploy Infrastructure

```bash
cd terraform

# Initialize Terraform
terraform init

# Review plan
terraform plan

# Deploy
terraform apply
```

This creates:
- ECS Fargate cluster and task definition
- IAM role for ECS task execution
- S3 bucket for reports
- EventBridge rule (daily at 8 AM UTC)
- CloudWatch log group

### 3. Deploy Cross-Account Roles

Deploy `EC2RightsizingAnalyzerRole` to all target accounts:

```bash
# Use Terraform or CloudFormation StackSets
cd terraform
terraform apply -target=module.cross_account_roles
```

### 4. Build and Push Docker Image

```bash
# Build image
docker build -t ec2-rightsizing-analyzer .

# Tag for ECR
docker tag ec2-rightsizing-analyzer:latest \
  123456789012.dkr.ecr.us-east-1.amazonaws.com/ec2-rightsizing-analyzer:latest

# Push to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789012.dkr.ecr.us-east-1.amazonaws.com

docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/ec2-rightsizing-analyzer:latest
```

### 5. Run Manually (Optional)

```bash
# Run locally
python src/analyzer.py --config config/accounts.yaml

# Run in ECS (one-time)
aws ecs run-task \
  --cluster ec2-rightsizing-cluster \
  --task-definition ec2-rightsizing-task \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

## Configuration

### Analysis Settings

Edit `config/accounts.yaml`:

```yaml
settings:
  # Lookback period for metrics (days)
  metrics_lookback_days: 14
  
  # Utilization thresholds
  thresholds:
    cpu_high: 80      # Consider upsizing if CPU > 80%
    cpu_low: 20       # Consider downsizing if CPU < 20%
    memory_high: 80
    memory_low: 20
  
  # Minimum savings to recommend (USD/month)
  min_savings_threshold: 50
  
  # Instance families to consider
  allowed_families:
    - m5
    - m6i
    - c5
    - c6i
    - r5
    - r6i
    - t3
    - t4g
```

## Output Reports

### Daily CSV Report

Stored in S3: `s3://ec2-rightsizing-reports/YYYY/MM/DD/report.csv`

```csv
account_id,account_name,instance_id,instance_type,region,avg_cpu,avg_memory,current_cost,recommended_type,new_cost,monthly_savings,annual_savings,team,environment
123456789012,Production,i-abc123,m5.2xlarge,us-east-1,15.2,22.5,280.32,m5.large,70.08,210.24,2522.88,platform,prod
123456789012,Production,i-def456,c5.4xlarge,us-east-1,85.6,78.2,544.32,c5.9xlarge,1224.72,-680.40,0,data,prod
```

### Summary Report

```
EC2 Rightsizing Analysis Report
Generated: 2024-08-15 08:00:00 UTC

Accounts Analyzed: 125
Total Instances: 3,847
Rightsizing Opportunities: 1,234 (32%)

Recommendations:
  - Downsize: 1,089 instances
  - Upsize: 145 instances
  - No change: 2,613 instances

Potential Savings:
  - Monthly: $287,450
  - Annual: $3,449,400

Top Opportunities:
  1. Production (123456789012): $45,200/month
  2. Analytics (234567890123): $38,900/month
  3. Development (345678901234): $22,100/month
```

## Scheduling

The ECS task runs automatically via EventBridge:

```hcl
# Daily at 8 AM UTC
schedule_expression = "cron(0 8 * * ? *)"
```

Modify in `terraform/eventbridge.tf` to change schedule.

## IAM Permissions

### Management Account (ECS Task Role)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sts:AssumeRole"
      ],
      "Resource": "arn:aws:iam::*:role/EC2RightsizingAnalyzerRole"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::ec2-rightsizing-reports/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "ce:GetCostForecast"
      ],
      "Resource": "*"
    }
  ]
}
```

### Target Accounts (Cross-Account Role)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeRegions",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:GetMetricData"
      ],
      "Resource": "*"
    }
  ]
}
```

## Cost

Running this solution costs approximately:
- **ECS Fargate**: ~$3/month (0.25 vCPU, 0.5 GB, 1 hour/day)
- **S3 Storage**: ~$1/month (assuming 10 GB reports)
- **CloudWatch Logs**: ~$1/month
- **Total**: ~$5/month

**ROI**: If you save even $500/month from rightsizing, that's a 100x return.

## Real-World Impact

At my previous organization:
- Analyzed 150+ AWS accounts with 5,000+ EC2 instances
- Identified $400K annual savings opportunities
- Automated monthly reporting to engineering teams
- Achieved 65% recommendation implementation rate
- Reduced average EC2 costs by 28%

## Monitoring

View logs in CloudWatch:

```bash
aws logs tail /ecs/ec2-rightsizing-analyzer --follow
```

Check task execution:

```bash
aws ecs list-tasks --cluster ec2-rightsizing-cluster
```

## Troubleshooting

### Cross-Account Role Issues

```bash
# Test role assumption
aws sts assume-role \
  --role-arn arn:aws:iam::123456789012:role/EC2RightsizingAnalyzerRole \
  --role-session-name test
```

### Missing Metrics

Ensure CloudWatch agent is installed on instances for memory metrics.

### High Costs

Reduce `metrics_lookback_days` or analyze fewer accounts per run.

## Contributing

Pull requests welcome! Please open an issue first.

## License

MIT License

## Author

Santosh Alete  
Cloud FinOps Engineer  
[LinkedIn](https://www.linkedin.com/in/santosh-r-alete-09260a27b/) | [GitHub](https://github.com/Santosh-Alete)
