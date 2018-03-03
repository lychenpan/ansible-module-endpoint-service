#!/usr/bin/python
# get_endpoint_service_arn: get and endpoint service which use the a specific
# network load balancer

DOCUMENTATION = '''
---
module: get_ocr_service_arn
description:
    - get endpoint service name of OCR
options:
    aws_access_key:
      description:
        - aws access key
      required: true
      default: null
    aws_secret_key:
      description:
        - aws secret key
      required: true
      default: null
    region:
      description:
        - regions support by AWS, valid values are ['us-east-1', 'us-west-2', 'us-west-1', 'eu-west-1', 
        'eu-central-1', 'ap-southeast-1', 'ap-northeast-1', 'ap-southeast-2', 'ap-northeast-2', 'ap-south-1',
         'sa-east-1']
      required: true
      default: null
'''

EXAMPLES = '''
- name: create endpoint service
  get_ocr_service_arn:
    aws_access_key: 
    aws_secret_key: 
    region: "ap-northeast-1"
    nlb_name: 
  register: eps_name

'''

try:
    import boto3
    import botocore
    HAS_BOTO3_API = True
except ImportError:
    HAS_BOTO3_API = False


class GetOCREnpointServiceName(object):

    def __init__(self, module):
        self.module = module
        self.aws_access_key = module.params.get('aws_access_key')
        self.aws_secret_key = module.params.get('aws_secret_key')
        self.region = module.params.get('region')
        self.nlb_name = module.params.get('nlb_name')

        if not HAS_BOTO3_API:
            self.module.fail_json(
                changed=False, msg='Python package boto3 is required')

        try:
            self.client = boto3.client(
                'ec2',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.region
            )

        except botocore.exceptions.ClientError as e:
            self.module.fail_json(
                changed=self.changed, msg='Cannot initialize connection to ec2: {}'.format(e))

    def process(self):
        response = self.client.describe_vpc_endpoint_service_configurations(
            DryRun=False
        )
        for service in response["ServiceConfigurations"]:
            for nlb_arns in service["NetworkLoadBalancerArns"]:
                if self.nlb_name in nlb_arns:
                    # here we use nlb name to locate our OCR endpoint service
                    return {"ServiceName": service["ServiceName"]}
        return {}


def main():
    module = AnsibleModule(
        argument_spec=dict(
            aws_access_key=dict(required=True, type='str'),
            aws_secret_key=dict(required=True, type='str', no_log=True),
            region=dict(choices=['us-east-1', 'us-west-2', 'us-west-1', 'eu-west-1', 'eu-central-1',
                                 'ap-southeast-1', 'ap-northeast-1', 'ap-southeast-2', 'ap-northeast-2', 'ap-south-1', 'sa-east-1']),
            nlb_name=dict(required=True, type='str')
        )
    )

    eps = GetOCREnpointServiceName(module)
    name = eps.process()
    module.exit_json(changed=False, **name)

from ansible.module_utils.basic import *
main()
