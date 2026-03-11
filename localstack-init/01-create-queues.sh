#!/bin/bash
# Runs automatically when LocalStack is ready.
# Creates the SQS queue used by ProcessShowdownQueueFunction.

awslocal sqs create-queue --queue-name showdown-queue
echo "showdown-queue created."
