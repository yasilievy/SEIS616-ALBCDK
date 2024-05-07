#!/bin/bash
yum update -y
yum install -y git httpd php
service httpd start
chkconfig httpd on
aws s3 cp s3://seis665-public/index.php /var/www/html/
