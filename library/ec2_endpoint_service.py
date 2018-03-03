#!/usr/bin/python
# ec2_endpoint_service: create endpoint service

DOCUMENTATION = '''
---
module: ec2_endpoint_service
description:
    - create endpoint service
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
    state:
      description:
        - Type of the state, valied values are ['present', 'absent']
      required: true
    nlb_arns:
      description:
        - Target environment
      required: true
      default: null
'''

EXAMPLES = '''
- name: create endpoint service
  ec2_endpoint_service:
    aws_access_key: 
    aws_secret_key:
    state: "present"
    region: "ap-northeast-1"
    nlb_arns:
      - '{{ nlb_out["LoadBalancers"][0]["LoadBalancerArn"] }}'
  register: eps_out

- debug: var=eps_out
'''

try:
    import boto3
    import botocore
    HAS_BOTO3_API = True
except ImportError:
    HAS_BOTO3_API = False


class EndPointService(object):

    def __init__(self, module):
        self.changed = False
        self.module = module
        self.aws_access_key = module.params.get('aws_access_key')
        self.aws_secret_key = module.params.get('aws_secret_key')
        self.region = module.params.get('region')
        self.state = module.params.get('state')
        self.nlb_arns = module.params.get('nlb_arns')

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
            self.elbv = boto3.client(
                'elbv2',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.region
            )

        except botocore.exceptions.ClientError as e:
            self.module.fail_json(
                changed=self.changed, msg='Cannot initialize connection to ec2: {}'.format(e))

    def pre_check(self):
        # TODO check whether nlb_arn exists; ****no need
        # check whether nlb_arn is used already
        eps_response = self.client.describe_vpc_endpoint_service_configurations(
            DryRun=False,
        )
        for service in eps_response["ServiceConfigurations"]:
            if self.nlb_arns[0] in service["NetworkLoadBalancerArns"]:
                self.module.fail_json(changed=False, msg="nlb has been used")
                return False
        return True

    def process(self):
        if self.state == 'present':
            self.__create__()
        elif self.state == 'absent':
            self.__delete__()
        self.module.exit_json(changed=self.changed)

    def __create__(self):
        eps_res = self.client.create_vpc_endpoint_service_configuration(
            #DryRun=True | False,
            AcceptanceRequired=False,
            NetworkLoadBalancerArns=self.nlb_arns
            # ClientToken='string'
        )
        eps_res['changed'] = True
        self.module.exit_json(**eps_res)

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
            nlb_arns=dict(required=True, type='list')
        )
    )

    changed = False

    eps = EndPointService(module)
    if eps.pre_check():
        eps.process()
    module.exit_json(changed=changed)

from ansible.module_utils.basic import *
main()
