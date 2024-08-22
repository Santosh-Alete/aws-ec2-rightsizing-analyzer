#!/usr/bin/env python3
"""
Cost calculator and instance type recommendations
"""

import logging

logger = logging.getLogger(__name__)

class CostCalculator:
    # Simplified pricing (USD/month for us-east-1)
    # In production, use AWS Pricing API
    PRICING = {
        't3.micro': 7.59,
        't3.small': 15.18,
        't3.medium': 30.37,
        't3.large': 60.74,
        't3.xlarge': 121.47,
        't3.2xlarge': 242.94,
        'm5.large': 70.08,
        'm5.xlarge': 140.16,
        'm5.2xlarge': 280.32,
        'm5.4xlarge': 560.64,
        'm5.8xlarge': 1121.28,
        'm5.12xlarge': 1681.92,
        'm5.16xlarge': 2242.56,
        'm5.24xlarge': 3363.84,
        'm6i.large': 69.35,
        'm6i.xlarge': 138.70,
        'm6i.2xlarge': 277.39,
        'm6i.4xlarge': 554.78,
        'm6i.8xlarge': 1109.57,
        'c5.large': 62.05,
        'c5.xlarge': 124.10,
        'c5.2xlarge': 248.20,
        'c5.4xlarge': 496.40,
        'c5.9xlarge': 1116.90,
        'c5.18xlarge': 2233.80,
        'r5.large': 91.98,
        'r5.xlarge': 183.96,
        'r5.2xlarge': 367.92,
        'r5.4xlarge': 735.84,
        'r5.8xlarge': 1471.68,
    }
    
    # Instance type hierarchy for recommendations
    INSTANCE_HIERARCHY = {
        't3': ['t3.micro', 't3.small', 't3.medium', 't3.large', 't3.xlarge', 't3.2xlarge'],
        'm5': ['m5.large', 'm5.xlarge', 'm5.2xlarge', 'm5.4xlarge', 'm5.8xlarge', 'm5.12xlarge', 'm5.16xlarge', 'm5.24xlarge'],
        'm6i': ['m6i.large', 'm6i.xlarge', 'm6i.2xlarge', 'm6i.4xlarge', 'm6i.8xlarge'],
        'c5': ['c5.large', 'c5.xlarge', 'c5.2xlarge', 'c5.4xlarge', 'c5.9xlarge', 'c5.18xlarge'],
        'r5': ['r5.large', 'r5.xlarge', 'r5.2xlarge', 'r5.4xlarge', 'r5.8xlarge'],
    }
    
    def get_instance_cost(self, instance_type, region='us-east-1'):
        """Get monthly cost for instance type"""
        return self.PRICING.get(instance_type, 0)
    
    def get_instance_family(self, instance_type):
        """Extract instance family (e.g., m5 from m5.2xlarge)"""
        return instance_type.split('.')[0]
    
    def get_smaller_instance(self, instance_type):
        """Get next smaller instance in same family"""
        family = self.get_instance_family(instance_type)
        
        if family not in self.INSTANCE_HIERARCHY:
            return instance_type
        
        hierarchy = self.INSTANCE_HIERARCHY[family]
        
        try:
            current_index = hierarchy.index(instance_type)
            if current_index > 0:
                return hierarchy[current_index - 1]
        except ValueError:
            pass
        
        return instance_type
    
    def get_larger_instance(self, instance_type):
        """Get next larger instance in same family"""
        family = self.get_instance_family(instance_type)
        
        if family not in self.INSTANCE_HIERARCHY:
            return instance_type
        
        hierarchy = self.INSTANCE_HIERARCHY[family]
        
        try:
            current_index = hierarchy.index(instance_type)
            if current_index < len(hierarchy) - 1:
                return hierarchy[current_index + 1]
        except ValueError:
            pass
        
        return instance_type
