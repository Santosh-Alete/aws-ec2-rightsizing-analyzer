#!/usr/bin/env python3
"""
CloudWatch metrics collector
"""

import boto3
import logging
from datetime import datetime, timedelta
from statistics import mean

logger = logging.getLogger(__name__)

class MetricsCollector:
    def __init__(self, config):
        self.config = config
        self.lookback_days = config['settings']['metrics_lookback_days']
    
    def collect_metrics(self, session, region, instance_id, instance_type):
        """Collect CloudWatch metrics for an instance"""
        cloudwatch = session.client('cloudwatch', region_name=region)
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=self.lookback_days)
        
        try:
            # CPU Utilization
            cpu_response = cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[
                    {'Name': 'InstanceId', 'Value': instance_id}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour
                Statistics=['Average']
            )
            
            cpu_datapoints = cpu_response.get('Datapoints', [])
            avg_cpu = mean([dp['Average'] for dp in cpu_datapoints]) if cpu_datapoints else 0
            
            # Memory Utilization (requires CloudWatch agent)
            try:
                memory_response = cloudwatch.get_metric_statistics(
                    Namespace='CWAgent',
                    MetricName='mem_used_percent',
                    Dimensions=[
                        {'Name': 'InstanceId', 'Value': instance_id}
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,
                    Statistics=['Average']
                )
                
                memory_datapoints = memory_response.get('Datapoints', [])
                avg_memory = mean([dp['Average'] for dp in memory_datapoints]) if memory_datapoints else 0
            except:
                avg_memory = 0  # Memory metrics not available
            
            return {
                'avg_cpu': avg_cpu,
                'avg_memory': avg_memory,
                'datapoints_count': len(cpu_datapoints)
            }
            
        except Exception as e:
            logger.error(f"    Error collecting metrics for {instance_id}: {e}")
            return None
