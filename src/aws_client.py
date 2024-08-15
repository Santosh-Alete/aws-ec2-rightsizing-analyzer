#!/usr/bin/env python3
"""
AWS Client wrapper with cross-account role assumption
"""

import boto3
import logging

logger = logging.getLogger(__name__)

class AWSClient:
    def __init__(self):
        self.sts_client = boto3.client('sts')
    
    def assume_role(self, account_id, role_name, region='us-east-1'):
        """Assume cross-account IAM role"""
        role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
        
        try:
            response = self.sts_client.assume_role(
                RoleArn=role_arn,
                RoleSessionName=f'ec2-rightsizing-{account_id}',
                DurationSeconds=3600
            )
            
            credentials = response['Credentials']
            
            session = boto3.Session(
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken'],
                region_name=region
            )
            
            logger.info(f"  Assumed role: {role_arn}")
            return session
            
        except Exception as e:
            logger.error(f"  Failed to assume role {role_arn}: {e}")
            return None
    
    def get_ec2_instances(self, session, region):
        """Get all running EC2 instances"""
        ec2 = session.client('ec2', region_name=region)
        
        try:
            response = ec2.describe_instances(
                Filters=[
                    {'Name': 'instance-state-name', 'Values': ['running']}
                ]
            )
            
            instances = []
            for reservation in response['Reservations']:
                instances.extend(reservation['Instances'])
            
            return instances
            
        except Exception as e:
            logger.error(f"  Error fetching instances: {e}")
            return []
