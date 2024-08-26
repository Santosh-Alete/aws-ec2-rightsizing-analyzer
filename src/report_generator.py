#!/usr/bin/env python3
"""
Report generator - CSV and summary reports
"""

import csv
import boto3
import logging
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

class ReportGenerator:
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.bucket_name = 'ec2-rightsizing-reports'  # From Terraform
    
    def generate_csv(self, recommendations):
        """Generate CSV report"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f'reports/ec2_rightsizing_{timestamp}.csv'
        
        fieldnames = [
            'account_id', 'account_name', 'instance_id', 'instance_type', 'region',
            'avg_cpu', 'avg_memory', 'current_cost', 'recommended_type', 'new_cost',
            'monthly_savings', 'annual_savings', 'action', 'team', 'environment'
        ]
        
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(recommendations)
        
        return filename
    
    def generate_summary(self, recommendations):
        """Generate text summary"""
        total_instances = len(recommendations)
        
        # Group by action
        actions = defaultdict(int)
        for rec in recommendations:
            actions[rec['action']] += 1
        
        # Calculate total savings
        total_monthly = sum(rec['monthly_savings'] for rec in recommendations)
        total_annual = sum(rec['annual_savings'] for rec in recommendations)
        
        # Group by account
        by_account = defaultdict(lambda: {'count': 0, 'savings': 0})
        for rec in recommendations:
            by_account[rec['account_name']]['count'] += 1
            by_account[rec['account_name']]['savings'] += rec['monthly_savings']
        
        # Sort accounts by savings
        top_accounts = sorted(
            by_account.items(),
            key=lambda x: x[1]['savings'],
            reverse=True
        )[:5]
        
        summary = f"""
EC2 Rightsizing Analysis Summary
{'=' * 70}
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

Total Recommendations: {total_instances}

Actions:
  - Downsize: {actions['downsize']} instances
  - Upsize: {actions['upsize']} instances

Potential Savings:
  - Monthly: ${total_monthly:,.2f}
  - Annual: ${total_annual:,.2f}

Top 5 Accounts by Savings:
"""
        
        for i, (account, data) in enumerate(top_accounts, 1):
            summary += f"  {i}. {account}: ${data['savings']:,.2f}/month ({data['count']} instances)\n"
        
        summary += "=" * 70
        
        return summary
    
    def upload_to_s3(self, local_file):
        """Upload report to S3"""
        date = datetime.utcnow()
        s3_key = f"{date.year}/{date.month:02d}/{date.day:02d}/{local_file.split('/')[-1]}"
        
        try:
            self.s3_client.upload_file(
                local_file,
                self.bucket_name,
                s3_key
            )
            return f"s3://{self.bucket_name}/{s3_key}"
        except Exception as e:
            logger.error(f"Failed to upload to S3: {e}")
            return None
