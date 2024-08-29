#!/usr/bin/env python3
"""
AWS EC2 Rightsizing Analyzer
Main orchestration logic
"""

import yaml
import logging
from datetime import datetime
from aws_client import AWSClient
from metrics_collector import MetricsCollector
from cost_calculator import CostCalculator
from report_generator import ReportGenerator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EC2RightsizingAnalyzer:
    def __init__(self, config_file='config/accounts.yaml'):
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.aws_client = AWSClient()
        self.metrics_collector = MetricsCollector(self.config)
        self.cost_calculator = CostCalculator()
        self.report_generator = ReportGenerator()
        
    def analyze_account(self, account):
        """Analyze all EC2 instances in an account"""
        account_id = account['account_id']
        account_name = account['name']
        role_name = account['role_name']
        
        logger.info(f"Analyzing account: {account_name} ({account_id})")
        
        recommendations = []
        
        for region in account['regions']:
            logger.info(f"  Region: {region}")
            
            # Assume cross-account role
            session = self.aws_client.assume_role(account_id, role_name, region)
            if not session:
                logger.error(f"  Failed to assume role in {account_id}")
                continue
            
            # Get all running instances
            instances = self.aws_client.get_ec2_instances(session, region)
            logger.info(f"  Found {len(instances)} instances")
            
            for instance in instances:
                instance_id = instance['InstanceId']
                instance_type = instance['InstanceType']
                
                # Collect metrics
                metrics = self.metrics_collector.collect_metrics(
                    session, region, instance_id, instance_type
                )
                
                if not metrics:
                    continue
                
                # Get current cost
                current_cost = self.cost_calculator.get_instance_cost(
                    instance_type, region
                )
                
                # Generate recommendation
                recommendation = self.generate_recommendation(
                    account_id, account_name, instance, metrics, current_cost, region
                )
                
                if recommendation:
                    recommendations.append(recommendation)
        
        return recommendations
    
    def generate_recommendation(self, account_id, account_name, instance, metrics, current_cost, region):
        """Generate rightsizing recommendation based on metrics"""
        instance_id = instance['InstanceId']
        instance_type = instance['InstanceType']
        
        avg_cpu = metrics['avg_cpu']
        avg_memory = metrics.get('avg_memory', 0)
        
        # Get tags
        tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
        team = tags.get('Team', 'Unknown')
        environment = tags.get('Environment', 'Unknown')
        
        # Thresholds from config
        thresholds = self.config['settings']['thresholds']
        cpu_low = thresholds['cpu_low']
        cpu_high = thresholds['cpu_high']
        
        # Determine recommendation
        recommended_type = None
        action = 'no_change'
        
        if avg_cpu < cpu_low and avg_memory < thresholds['memory_low']:
            # Downsize
            recommended_type = self.cost_calculator.get_smaller_instance(instance_type)
            action = 'downsize'
        elif avg_cpu > cpu_high or avg_memory > thresholds['memory_high']:
            # Upsize
            recommended_type = self.cost_calculator.get_larger_instance(instance_type)
            action = 'upsize'
        
        if not recommended_type or recommended_type == instance_type:
            return None
        
        # Calculate savings
        new_cost = self.cost_calculator.get_instance_cost(recommended_type, region)
        monthly_savings = current_cost - new_cost
        
        # Filter by minimum savings threshold
        if monthly_savings < self.config['settings']['min_savings_threshold']:
            return None
        
        annual_savings = monthly_savings * 12
        
        return {
            'account_id': account_id,
            'account_name': account_name,
            'instance_id': instance_id,
            'instance_type': instance_type,
            'region': region,
            'avg_cpu': round(avg_cpu, 2),
            'avg_memory': round(avg_memory, 2),
            'current_cost': round(current_cost, 2),
            'recommended_type': recommended_type,
            'new_cost': round(new_cost, 2),
            'monthly_savings': round(monthly_savings, 2),
            'annual_savings': round(annual_savings, 2),
            'action': action,
            'team': team,
            'environment': environment
        }
    
    def run(self):
        """Main execution"""
        logger.info("=" * 70)
        logger.info("EC2 Rightsizing Analysis Started")
        logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
        logger.info("=" * 70)
        
        all_recommendations = []
        
        for account in self.config['accounts']:
            try:
                recommendations = self.analyze_account(account)
                all_recommendations.extend(recommendations)
            except Exception as e:
                logger.error(f"Error analyzing account {account['name']}: {e}")
                continue
        
        # Generate reports
        logger.info(f"\nTotal recommendations: {len(all_recommendations)}")
        
        if all_recommendations:
            # Generate CSV report
            csv_file = self.report_generator.generate_csv(all_recommendations)
            logger.info(f"CSV report: {csv_file}")
            
            # Generate summary
            summary = self.report_generator.generate_summary(all_recommendations)
            logger.info(f"\n{summary}")
            
            # Upload to S3
            s3_path = self.report_generator.upload_to_s3(csv_file)
            logger.info(f"Uploaded to S3: {s3_path}")
        
        logger.info("=" * 70)
        logger.info("Analysis Complete")
        logger.info("=" * 70)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='EC2 Rightsizing Analyzer')
    parser.add_argument('--config', default='config/accounts.yaml', help='Config file')
    
    args = parser.parse_args()
    
    analyzer = EC2RightsizingAnalyzer(config_file=args.config)
    analyzer.run()
