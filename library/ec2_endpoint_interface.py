#!/usr/bin/python
# ec2_endpoint_service: create endpoint service

DOCUMENTATION = '''
---
module: ec2_endpoint_interface
description:
    - create endpoint interface
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
    .... refer example
'''

EXAMPLES = '''
- name: create endpoint interface
  ec2_endpoint_interface:
    aws_access_key:
    aws_secret_key:
    state: "present"
    region: "ap-northeast-1"
    vpc_id: 
    service_name:
    security_group_ids:
        - ****
    subnet_ids:
        - ****
'''

try:
    import boto3
    import botocore
    HAS_BOTO3_API = True
except ImportError:
    HAS_BOTO3_API = False


class EndPointInterface(object):

    def __init__(self, module):
        self.changed = False
        self.module = module
        self.aws_access_key = module.params.get('aws_access_key')
        self.aws_secret_key = module.params.get('aws_secret_key')
        self.region = module.params.get('region')
        self.state = module.params.get('state')
        self.vpc_id = module.params.get('vpc_id')
        self.service_name = module.params.get('service_name')
        self.security_group_ids = module.params.get('security_group_ids')
        self.subnet_ids = module.params.get('subnet_ids')

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

    def pre_check(self):
        """check whether the endpoint interface existed or not; 
         TODO:  should check what happened when create multi times for same service parameters
        """
        print "Not implemented"

    def process(self):
        if self.state == 'present':
            self.__create__()
        elif self.state == 'absent':
            self.__delete__()
        self.module.exit_json(changed=self.changed)

    def __create__(self):
        response = self.client.create_vpc_endpoint(
            DryRun=True | False,
            VpcEndpointType='Interface',
            VpcId=self.vpc_id,
            ServiceName=self.service_name,
            SubnetIds=self.subnet_ids,
            SecurityGroupIds=self.security_group_ids,
            PrivateDnsEnabled=True
        )

        self.module.exit_json(**response)

    def __delete__(self):
        print "Not implemented"


def main():
    module = AnsibleModule(
        argument_spec=dict(
            aws_access_key=dict(required=True, type='str'),
            aws_secret_key=dict(required=True, type='str', no_log=True),
            region=dict(choices=['us-east-1', 'us-west-2', 'us-west-1', 'eu-west-1', 'eu-central-1',
                                 'ap-southeast-1', 'ap-northeast-1', 'ap-southeast-2', 'ap-northeast-2', 'ap-south-1', 'sa-east-1']),
            state=dict(choices=['present', 'absent']),
            vpc_id=dict(required=True, type='str'),
            service_name=dict(required=True, type='str'),
            security_group_ids=dict(required=True, type='list'),
            subnet_ids=dict(required=True, type='list')
        )
    )

    changed = False

    eps = EndPointInterface(module)
    # eps.pre_check()
    eps.process()

    module.exit_json(changed=changed)

from ansible.module_utils.basic import *
main()
