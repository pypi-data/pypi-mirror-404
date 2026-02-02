"""
S3 resource collector.
"""

import boto3
from typing import List, Dict, Any, Optional


def collect_s3_resources(session: boto3.Session, region: Optional[str], account_id: str) -> List[Dict[str, Any]]:
    """
    Collect S3 buckets. S3 is a global service but buckets exist in regions.

    Args:
        session: boto3.Session to use
        region: Not used for S3 (global service)
        account_id: AWS account ID

    Returns:
        List of resource dictionaries
    """
    resources = []
    s3 = session.client('s3')

    # List all buckets
    try:
        response = s3.list_buckets()
        buckets = response.get('Buckets', [])
    except Exception:
        return resources

    for bucket in buckets:
        bucket_name = bucket['Name']
        creation_date = bucket.get('CreationDate')

        # Get bucket location
        bucket_region = 'us-east-1'  # Default
        try:
            loc_response = s3.get_bucket_location(Bucket=bucket_name)
            loc = loc_response.get('LocationConstraint')
            if loc:
                bucket_region = loc
        except Exception:
            pass

        # Get bucket tags
        tags = {}
        try:
            tag_response = s3.get_bucket_tagging(Bucket=bucket_name)
            for tag in tag_response.get('TagSet', []):
                tags[tag.get('Key', '')] = tag.get('Value', '')
        except Exception:
            pass

        # Get versioning status
        versioning = None
        try:
            ver_response = s3.get_bucket_versioning(Bucket=bucket_name)
            versioning = ver_response.get('Status')
        except Exception:
            pass

        # Get encryption configuration
        encryption = None
        try:
            enc_response = s3.get_bucket_encryption(Bucket=bucket_name)
            rules = enc_response.get('ServerSideEncryptionConfiguration', {}).get('Rules', [])
            if rules:
                encryption = rules[0].get('ApplyServerSideEncryptionByDefault', {}).get('SSEAlgorithm')
        except Exception:
            pass

        # Get public access block
        public_access_blocked = None
        try:
            pab_response = s3.get_public_access_block(Bucket=bucket_name)
            config = pab_response.get('PublicAccessBlockConfiguration', {})
            public_access_blocked = all([
                config.get('BlockPublicAcls', False),
                config.get('IgnorePublicAcls', False),
                config.get('BlockPublicPolicy', False),
                config.get('RestrictPublicBuckets', False)
            ])
        except Exception:
            pass

        resources.append({
            'service': 's3',
            'type': 'bucket',
            'id': bucket_name,
            'arn': f"arn:aws:s3:::{bucket_name}",
            'name': bucket_name,
            'region': bucket_region,
            'details': {
                'creation_date': str(creation_date) if creation_date else None,
                'versioning': versioning,
                'encryption': encryption,
                'public_access_blocked': public_access_blocked,
            },
            'tags': tags
        })

    return resources
