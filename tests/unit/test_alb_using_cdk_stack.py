import aws_cdk as core
import aws_cdk.assertions as assertions

from alb_using_cdk.alb_using_cdk_stack import AlbUsingCdkStack

# example tests. To run these tests, uncomment this file along with the example
# resource in alb_using_cdk/alb_using_cdk_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AlbUsingCdkStack(app, "alb-using-cdk")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
