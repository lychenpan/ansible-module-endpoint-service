#!/usr/bin/python
# aws_nlb: create network load balancer and configuration

DOCUMENTATION = '''
---
module: aws_nlb
description:
    - create nlb and related confgiuration, this is used to create endpoint service
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
        - regions support by AWS, valid values are ['us-east-1', 'us-west-2', 'us-west-1', 'eu-west-1', 'eu-central-1', 'ap-southeast-1', 'ap-northeast-1', 'ap-southeast-2', 'ap-northeast-2', 'ap-south-1', 'sa-east-1']
      required: true
      default: null
    vpc_id:
      description:
        - VPC id for security group
      required: true
      default: null
    state:
      description:
        - Type of the state, valied values are ['present', 'absent']
      required: true
    #TODO
'''

EXAMPLES = '''
- name: create nlb and related configuration
  aws_nlb:
    aws_access_key: 
    aws_secret_key: 
    region: ap-northeast-1
    vpc_id: 
    name: name
    state: present
    subnets:
        - subnet1
        - subnet2
    #TODO: maybe need listeners
    listener:
        - port: 80
          target_groups:
            - name: target_group_name
              targets:
                  - Id: IP address,
                    Port: Not required
                    AvailabilityZone: Not required
'''

try:
    import boto3
    import botocore
    HAS_BOTO3_API = True
except ImportError:
    HAS_BOTO3_API = False


class NetworkLoadBalancer(object):

    def __init__(self, module):
        self.changed = False
        self.module = module
        self.aws_access_key = module.params.get('aws_access_key')
        self.aws_secret_key = module.params.get('aws_secret_key')
        self.region = module.params.get('region')
        self.vpc_id = module.params.get('vpc_id')

        self.state = module.params.get('state')
        self.subnets = module.params.get('subnets')  # it will be a list
        self.name = module.params.get('name')
        self.listener = module.params.get('listener')

        if not HAS_BOTO3_API:
            self.module.fail_json(
                changed=False, msg='Python package boto3 is required')

        try:
            self.client = boto3.client(
                'elbv2',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.region
            )

        except botocore.exceptions.ClientError as e:
            self.module.fail_json(
                changed=self.changed, msg='Cannot initialize connection to ec2: {}'.format(e))

        # check whether current load balancer exists

    def __create_nlb__(self):
        """create network load balancer; and create liseter"""
        lb_response = self.client.create_load_balancer(
            Name=self.name,
            # need test
            Subnets=self.subnets,
            Scheme='internal',
            Type='network'
        )
        # TODO test the reponse's vpcid same with self.vpc_id; self.changed =
        # true
        return lb_response

    def process(self):
        # TODO use describe to check whether exists
        if self.state == 'present':
            res = self.__create__()
        elif self.state == 'absent':
            res = self.__delete_()
        res['changed'] = self.changed
#         if lb_out.LoadBalancers[0].State.Code == "active":
#             self.module.exit_json(**res)
#         else:
#             self.module.fail_json(**res)
        self.module.exit_json(**res)

    def __create__(self):
        # create listener for nlb
        lb_res = self.__create_nlb__()
        # TODO currently we assum only one listener
        listenerd = self.listener[0]

        rg_res = self.__create_register_target_group__(
            listenerd['target_groups'])

        actions = [{'Type': 'forward',
                    'TargetGroupArn': x['target_group_res']['TargetGroups'][0]['TargetGroupArn']}
                   for x in rg_res]

        ls_res = self.client.create_listener(
            LoadBalancerArn=lb_res['LoadBalancers'][0]['LoadBalancerArn'],
            Protocol='TCP',
            Port=listenerd['port'],
            DefaultActions=actions
        )
        lb_res.update(ls_res)
        # here we didn't return register target group result
        return lb_res

    def __create_register_target_group__(self, target_groups):
        # create target group and register its targets to related group
        res_combine = []
        for target_group in target_groups:
            tg = self.client.create_target_group(
                Name=target_group['name'],
                Protocol='TCP',  # only available one for NLB
                Port=80,
                VpcId=self.vpc_id,
                # here we use IP, because NLB has limitation in instance type
                TargetType='ip'
            )
            # register the targets with the created target group
            rg_tg = self.client.register_targets(
                TargetGroupArn=tg['TargetGroups'][0]['TargetGroupArn'],
                # TODO test whether need to create the targets list explicitly
                Targets=target_group['targets']
            )
            res_combine.append({
                "target_group_res": tg,
                "register_targets_res": rg_tg
            })
        return res_combine

    # TODO  delete all existed resource about nlb
    def __delete__(self):
        # TODO
        print "not implemented"


def main():
    module = AnsibleModule(
        argument_spec=dict(
            aws_access_key=dict(required=True, type='str'),
            aws_secret_key=dict(required=True, type='str', no_log=True),
            region=dict(choices=['us-east-1', 'us-west-2', 'us-west-1', 'eu-west-1', 'eu-central-1',
                                 'ap-southeast-1', 'ap-northeast-1', 'ap-southeast-2', 'ap-northeast-2', 'ap-south-1', 'sa-east-1']),
            vpc_id=dict(required=True, type='str'),
            name=dict(required=True, type='str'),
            subnets=dict(required=True, type='list'),
            state=dict(choices=['present', 'absent']),
            listener=dict(required=True, type='list')
        )
    )

    changed = False
    nlb_conn = NetworkLoadBalancer(module)
    nlb_conn.process()
    module.exit_json(changed=changed,)

from ansible.module_utils.basic import *
main()
