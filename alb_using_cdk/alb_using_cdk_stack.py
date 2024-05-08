from aws_cdk.aws_s3_assets import Asset as S3asset
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_rds as rds,
    aws_elasticloadbalancingv2 as elbv2,
    CfnOutput
    
)
from constructs import Construct
import os.path

class AlbUsingCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str,cdk_lab_vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # instantiating the vpc
        # my_network_vpc = ec2.Vpc(self,"EngineeringVPC",
        #     ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/18"),
        #                     subnet_configuration=[ec2.SubnetConfiguration(name="public_subnets",subnet_type=ec2.SubnetType.PUBLIC)])#,
                            # ec2.SubnetConfiguration(name="PublicSubnet02",subnet_type=ec2.SubnetType.PUBLIC)])
                            
        # public_subnet_1 = ec2.PublicSubnet(self,"PublicSubnet01",cidr_block="10.0.0.0/24",availability_zone="us-east-1a",vpc_id=my_network_vpc.vpc_id)
        
        # public_subnet_2 = ec2.PublicSubnet(self,"PublicSubnet02",cidr_block="10.0.1.0/24",availability_zone="us-east-1b",vpc_id=my_network_vpc.vpc_id)
        
        # internet_gateway = ec2.CfnInternetGateway(self,"internet_gateway")
        
        # vpc_gateway_attachment_1 = ec2.CfnVPCGatewayAttachment(self,"vpc_gateway_attachment", internet_gateway_id=internet_gateway.attr_internet_gateway_id, vpc_id="EngineeringVPC")
        
        public_route_table_1 = ec2.CfnRouteTable(self,"public_route_table",vpc_id=cdk_lab_vpc.vpc_id)
        
        public_route = ec2.CfnRoute(self,"public_route",route_table_id=public_route_table_1.attr_route_table_id,gateway_id=cdk_lab_vpc.internet_gateway_id,destination_cidr_block="0.0.0.0/0")
        
        # public_subnet_rt_assoc_1 = ec2.CfnSubnetRouteTableAssociation(self,"PublicSubnet1RTassoc",route_table_id=public_route_table_1.attr_route_table_id,subnet_id=public_subnet_1.subnet_id)
        
        # public_subnet_rt_assoc_2 = ec2.CfnSubnetRouteTableAssociation(self,"PublicSubnet2RTassoc",route_table_id=public_route_table_1.attr_route_table_id,subnet_id=public_subnet_2.subnet_id)
        
        public_subnet_rt_assoc_1 = ec2.CfnSubnetRouteTableAssociation(self,"PublicSubnet1RTassoc",route_table_id=public_route_table_1.attr_route_table_id,subnet_id=cdk_lab_vpc.select_subnets(subnet_type=ec2.SubnetType.PUBLIC).subnet_ids[0])
        
        public_subnet_rt_assoc_2 = ec2.CfnSubnetRouteTableAssociation(self,"PublicSubnet2RTassoc",route_table_id=public_route_table_1.attr_route_table_id,subnet_id=cdk_lab_vpc.select_subnets(subnet_type=ec2.SubnetType.PUBLIC).subnet_ids[1])
    
    
        
        # instantiating the IAM policies
        InstanceRole = iam.Role(self,"InstanceSSM",assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"))
        InstanceRole.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMmanagedInstanceCore"))
        
        # create an ec2 instance
        web_instance_1 = ec2.Instance(self,"web_instance_1",
                                            vpc=cdk_lab_vpc,
                                            instance_type=ec2.InstanceType("t2.micro"),
                                            machine_image=ec2.AmazonLinuxImage(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),
                                            role=InstanceRole,
                                            vpc_subnets=ec2.SubnetSelection(subnet_group_name="PublicSubnet01"))
                                            
                                            
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
        
        
                
        # create an ec2 instance
        web_instance_2 = ec2.Instance(self,"web_instance_2",
                                            vpc=cdk_lab_vpc,
                                            instance_type=ec2.InstanceType("t2.micro"),
                                            machine_image=ec2.AmazonLinuxImage(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),
                                            role=InstanceRole)#,
                                            # vpc_subnets=ec2.SubnetSelection(subnet_group_name="PublicSubnet02"))
                                            
        security_group_1 = ec2.SecurityGroup(self,"WebserversSG",vpc=cdk_lab_vpc)
        
        security_group_1.add_ingress_rule(peer=ec2.Peer.ipv4("0.0.0.0/0"),connection=ec2.Port.tcp(80))

        your_ip_address = "75.73.137.183"

        security_group_1.add_ingress_rule(peer=ec2.Peer.ipv4(your_ip_address),connection=ec2.Port.tcp(22))
        
        application_load_balancerv2 = elbv2.ApplicationLoadBalancer(self,"EngineeringLB",vpc=cdk_lab_vpc,security_group=security_group_1,internet_facing=True)
        
        listener = application_load_balancerv2.add_listneer("Listener", port=80)
        listener.add_targets("Target",port=80)
        
        # target_group_1 = elbv2.CfnTargetGroup(self,"EngineeringWebservers",
        #     health_check_enabled=True,
        #     health_check_port="80",
        #     health_check_protocol="HTTP",
        #     vpc_id=cdk_lab_vpc.vpc_id,
        #     port=80,
        #     protocol="HTTP",
        #     targets=[elbv2.CfnTargetGroup.TargetDescriptionProperty(id="web_instance_1")]
        #     )
        
        # listener_1 = application_load_balancerv2.add_listener(self,"Listener",port=80)
        
        
        
        
        
        CfnOutput(self, "ALB DNS name: ", value=application_load_balancerv2.load_balancer_dns_name)
        CfnOutput(self, "URL: ", value='http://'+application_load_balancerv2.load_balancer_dns_name)
        
        # upload_bucket_name = CfnParameter(self, "uploadBucketName", type="String",
        #     description="The name of the Amazon S3 bucket where uploaded files will be stored.")
        

    