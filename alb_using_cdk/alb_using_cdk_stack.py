from aws_cdk.aws_s3_assets import Asset as S3asset
from aws_cdk import (
    # Duration,
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_rds as rds
    # aws_sqs as sqs,
)
from constructs import Construct
import os.path

class AlbUsingCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # instantiating the vpc
        my_network_vpc = ec2.Vpc(self,"my_network_vpc",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/18"),
                            subnet_configuration=[ec2.SubnetConfiguration(name="PublicSubnet01",subnet_type=ec2.SubnetType.PUBLIC),
                            ec2.SubnetConfiguration(name="PublicSubnet02",subnet_type=ec2.SubnetType.PUBLIC)])
        
        # instantiating the IAM policies
        InstanceRole = iam.Role(self,"InstanceSSM",assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"))
        InstanceRole.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMmanagedInstanceCore"))
        
        # create an ec2 instance
        my_web_server_instance = ec2.Instance(self,"my_web_server_instance",
                                            vpc=my_network_vpc,
                                            instance_type=ec2.InstanceType("t2.micro"),
                                            machine_image=ec2.AmazonLinuxImage(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),
                                            role=InstanceRole,
                                            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC))
                                            
        
        
        dirname = os.path.dirname(__file__)
        
        # script in s3 as asset 
        webinitscriptasset = S3asset(self, "Asset", path=os.path.join(dirname, "configure.sh"))
        asset_path = my_web_server_instance.user_data.add_s3_download_command(
            bucket=webinitscriptasset.bucket,
            bucket_key=webinitscriptasset.s3_object_key
            )
            
        # userdata execution
        
        my_web_server_instance.user_data.add_execute_file_command(
            file_path = asset_path
            )
        webinitscriptasset.grant_read(my_web_server_instance.role)
        
        # allow inbound HTTP traffic in security group
        my_web_server_instance.connections.allow_from_any_ipv4(ec2.Port.tcp(80))
        

    