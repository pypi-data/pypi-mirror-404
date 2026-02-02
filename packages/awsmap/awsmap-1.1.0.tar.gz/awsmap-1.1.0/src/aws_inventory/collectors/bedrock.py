"""
Bedrock resource collector.
"""

import boto3
from typing import List, Dict, Any, Optional


def collect_bedrock_resources(session: boto3.Session, region: Optional[str], account_id: str) -> List[Dict[str, Any]]:
    """
    Collect Bedrock resources: custom models, model customization jobs, provisioned throughput.

    Args:
        session: boto3.Session to use
        region: AWS region
        account_id: AWS account ID

    Returns:
        List of resource dictionaries
    """
    resources = []
    bedrock = session.client('bedrock', region_name=region)

    # Custom Models
    try:
        paginator = bedrock.get_paginator('list_custom_models')
        for page in paginator.paginate():
            for model in page.get('modelSummaries', []):
                model_arn = model['modelArn']
                model_name = model['modelName']

                try:
                    # Get model details
                    model_response = bedrock.get_custom_model(modelIdentifier=model_arn)

                    resources.append({
                        'service': 'bedrock',
                        'type': 'custom-model',
                        'id': model_name,
                        'arn': model_arn,
                        'name': model_name,
                        'region': region,
                        'details': {
                            'base_model_arn': model_response.get('baseModelArn'),
                            'customization_type': model_response.get('customizationType'),
                            'creation_time': str(model_response.get('creationTime', '')),
                            'job_arn': model_response.get('jobArn'),
                            'training_data_config': model_response.get('trainingDataConfig'),
                            'output_data_config': model_response.get('outputDataConfig'),
                        },
                        'tags': {}
                    })
                except Exception:
                    pass
    except Exception:
        pass

    # Model Customization Jobs (active)
    try:
        paginator = bedrock.get_paginator('list_model_customization_jobs')
        for page in paginator.paginate():
            for job in page.get('modelCustomizationJobSummaries', []):
                job_arn = job['jobArn']
                job_name = job['jobName']

                # Only include active jobs
                status = job.get('status')
                if status in ['Completed', 'Failed', 'Stopped']:
                    continue

                resources.append({
                    'service': 'bedrock',
                    'type': 'customization-job',
                    'id': job_name,
                    'arn': job_arn,
                    'name': job_name,
                    'region': region,
                    'details': {
                        'status': status,
                        'base_model_arn': job.get('baseModelArn'),
                        'customization_type': job.get('customizationType'),
                        'creation_time': str(job.get('creationTime', '')),
                        'end_time': str(job.get('endTime', '')) if job.get('endTime') else None,
                        'last_modified_time': str(job.get('lastModifiedTime', '')),
                        'custom_model_arn': job.get('customModelArn'),
                        'custom_model_name': job.get('customModelName'),
                    },
                    'tags': {}
                })
    except Exception:
        pass

    # Provisioned Model Throughput
    try:
        paginator = bedrock.get_paginator('list_provisioned_model_throughputs')
        for page in paginator.paginate():
            for pmt in page.get('provisionedModelSummaries', []):
                pmt_arn = pmt['provisionedModelArn']
                pmt_name = pmt['provisionedModelName']

                try:
                    # Get provisioned throughput details
                    pmt_response = bedrock.get_provisioned_model_throughput(
                        provisionedModelId=pmt_arn
                    )

                    # Get tags
                    tags = {}
                    try:
                        tag_response = bedrock.list_tags_for_resource(resourceARN=pmt_arn)
                        for tag in tag_response.get('tags', []):
                            tags[tag.get('key', '')] = tag.get('value', '')
                    except Exception:
                        pass

                    resources.append({
                        'service': 'bedrock',
                        'type': 'provisioned-throughput',
                        'id': pmt_name,
                        'arn': pmt_arn,
                        'name': pmt_name,
                        'region': region,
                        'details': {
                            'status': pmt_response.get('status'),
                            'model_arn': pmt_response.get('modelArn'),
                            'desired_model_arn': pmt_response.get('desiredModelArn'),
                            'foundation_model_arn': pmt_response.get('foundationModelArn'),
                            'model_units': pmt_response.get('modelUnits'),
                            'desired_model_units': pmt_response.get('desiredModelUnits'),
                            'commitment_duration': pmt_response.get('commitmentDuration'),
                            'commitment_expiration_time': str(pmt_response.get('commitmentExpirationTime', '')) if pmt_response.get('commitmentExpirationTime') else None,
                            'creation_time': str(pmt_response.get('creationTime', '')),
                            'last_modified_time': str(pmt_response.get('lastModifiedTime', '')),
                        },
                        'tags': tags
                    })
                except Exception:
                    pass
    except Exception:
        pass

    # Guardrails
    try:
        paginator = bedrock.get_paginator('list_guardrails')
        for page in paginator.paginate():
            for guardrail in page.get('guardrails', []):
                guardrail_id = guardrail['id']
                guardrail_arn = guardrail['arn']
                guardrail_name = guardrail['name']

                # Get tags
                tags = {}
                try:
                    tag_response = bedrock.list_tags_for_resource(resourceARN=guardrail_arn)
                    for tag in tag_response.get('tags', []):
                        tags[tag.get('key', '')] = tag.get('value', '')
                except Exception:
                    pass

                resources.append({
                    'service': 'bedrock',
                    'type': 'guardrail',
                    'id': guardrail_id,
                    'arn': guardrail_arn,
                    'name': guardrail_name,
                    'region': region,
                    'details': {
                        'status': guardrail.get('status'),
                        'version': guardrail.get('version'),
                        'created_at': str(guardrail.get('createdAt', '')),
                        'updated_at': str(guardrail.get('updatedAt', '')),
                    },
                    'tags': tags
                })
    except Exception:
        pass

    return resources
