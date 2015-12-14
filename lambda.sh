# !/usr/bin/bash

set -e
set -x

rm -rf dist dist.zip permits/*.pyc
cp -r permits dist
cp -r .env/lib/python2.7/site-packages/* dist
cd dist && zip -9r ../dist.zip *
cd ..

# aws lambda create-function \
# --region us-west-2 \
# --function-name construction-permits \
# --zip-file fileb://dist.zip \
# --role arn:aws:iam::994940854184:role/lambda_basic_execution \
# --handler permits.main \
# --runtime python2.7 \
# --profile permits \
# --timeout 300 \
# --memory-size 128

aws lambda update-function-code \
--function-name construction-permits \
--zip-file fileb://dist.zip \
--publish

# aws lambda update-function-configuration \
# --function-name construction-permits \
# --timeout 300 \
# --handler permits.handler

aws lambda invoke \
--invocation-type Event \
--function-name construction-permits \
--region us-west-2 \
--profile permits
