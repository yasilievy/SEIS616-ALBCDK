from aws_cdk.aws_s3_assets import Asset as S3asset
from aws_cdk import (
    # Duration,
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_rds as rds,
    aws_elasticloadblancingv2 as elbv2,
    CfOutput as output
    # aws_sqs as sqs,
)
from constructs import Construct
import os.path

class AlbUsingCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # instantiating the vpc
        my_network_vpc = ec2.Vpc(self,"EngineeringVPC",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/18"),
                            subnet_configuration=[ec2.SubnetConfiguration(name="PublicSubnet01",subnet_type=ec2.SubnetType.PUBLIC),
                            ec2.SubnetConfiguration(name="PublicSubnet02",subnet_type=ec2.SubnetType.PUBLIC)])
        
        internet_gateway = ec2.CfnInternetGateway(self,"internet_gateway")
        
        vpc_gateway_attachment = ec2.CfnVPCGatewayAttachment(self,"vpc_gateway_attachment", internet_gateway_id = "internet_gateway")
        
        my_security_group = ec2.SecurityGroup(self,"EngineeringVpc",vpc=my_network_vpc)
        
        public_route_table = ec2.CfnRouteTable(self,"public_route_table",vpc_id="EngineeringVPC")
        
        public_route = ec2.CfnRoute(self,"public_route",route_table_id="public_route_table",gateway_id="internet_gateway")
        
        public_subnet_rt_assoc_1 = ec2.CfnSubnetRouteTableAssociation(self,"PublicSubnet1RTassoc",route_table_id="public_route_table",subnet_id =ec2.SubnetSelection(name="PublicSubnet01"))
        
        public_subnet_rt_assoc_2 = ec2.CfnSubnetRouteTableAssociation(self,"PublicSubnet2RTassoc",route_table_id="public_route_table",subnet_id =ec2.SubnetSelection(name="PublicSubnet02"))
        
        
        # instantiating the IAM policies
        InstanceRole = iam.Role(self,"InstanceSSM",assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"))
        InstanceRole.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMmanagedInstanceCore"))
        
        # create an ec2 instance
        web_instance_1 = ec2.Instance(self,"web_instance_1",
                                            vpc=my_network_vpc,
                                            instance_type=ec2.InstanceType("t2.micro"),
                                            machine_image=ec2.AmazonLinuxImage(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),
                                            role=InstanceRole,
                                            vpc_subnets=ec2.SubnetSelection(name="PublicSubnet01"))
        
                
        # create an ec2 instance
        web_instance_2 = ec2.Instance(self,"web_instance_2",
                                            vpc=my_network_vpc,
                                            instance_type=ec2.InstanceType("t2.micro"),
                                            machine_image=ec2.AmazonLinuxImage(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),
                                            role=InstanceRole,
                                            vpc_subnets=ec2.SubnetSelection(name="PublicSubnet02"))
                                            
        security_group_1 = ec2.SecurityGroup(self,"WebserversSG",vpc_id = "EngineeringVPC")
        
        application_load_balancerv2 = elbv2.ApplicationLoadBalancer(self,"EngineeringLB",vpc=my_network_vpc,security_group=security_group_1,internet_facing=True)
        
        target_group_1 = elbv2.CfnTargetGroup(self,"EngineeringWebservers",
            HealthCheckEnabled=True,
            HealthCheckPort=80,
            HealthCheckProtocol="HTTP",
            vpc_id="EngineeringVPC",
            port=80,
            protocol="HTTP",
            targets=[elbv2.CfnTargetGroup.TargetDescriptionProperty(id="web_instance_1")]
            )
        
        listener_1 = application_load_balancev2.add_listener("Listener",port=80)
        
        
        
        
        dirname = os.path.dirname(__file__)
        
        # script in s3 as asset 
        webinitscriptasset = S3asset(self, "Asset", path=os.path.join(dirname, "configure.sh"))
        asset_path = web_instance_1.user_data.add_s3_download_command(
            bucket=webinitscriptasset.bucket,
            bucket_key=webinitscriptasset.s3_object_key
            )
            
        # userdata execution
        
        web_instance_1.user_data.add_execute_file_command(
            file_path = asset_path
            )
        webinitscriptasset.grant_read(web_instance_1.role)
        
        
        
        # upload_bucket_name = CfnParameter(self, "uploadBucketName", type="String",
        #     description="The name of the Amazon S3 bucket where uploaded files will be stored.")
        

    