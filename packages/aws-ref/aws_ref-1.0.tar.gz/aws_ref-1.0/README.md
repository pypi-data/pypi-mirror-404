# aws-ref : AWS IAM Service Reference Helper CLI

A powerful CLI tool designed for AWS Cloud Engineers to explore IAM actions and understand their condition key support - perfect for writing CloudFormation templates and IAM policies!

## Problem It Solves

As an AWS Cloud Engineer, you know the pain of:
- Not knowing which IAM actions support `aws:RequestTag/${TagKey}`
- Being unsure if `aws:ResourceTag/${TagKey}` works with a specific action
- Wondering if `aws:TagKeys` condition is supported
- Trying to figure out which actions support `aws:SourceArn` conditions
- Debugging CloudFormation templates due to invalid condition keys

**aws-ref** solves all of this by providing instant, human-readable information about every IAM action across all AWS services!

## Features

-  **Search Actions**: Find IAM actions for any AWS service
-  **Tag Support Detection**: Instantly see if an action supports RequestTag, ResourceTag, or TagKeys
-  **ARN Conditions**: Check for SourceArn and SourceAccount support
-  **Policy Generation**: Generate example IAM policies with condition keys
-  **Complete Coverage**: Access data for all AWS services
-  **Fast**: Direct API calls to AWS Service Reference

## Installation

### Using pip (Recommended)

```bash
pip3 install aws-ref
```

### From Source

```bash
git clone https://github.com/yourusername/aws-ref.git
cd aws-ref
pip3 install -e .
```

## Quick Start

### List All AWS Services

```bash
aws-ref --list
```

### Explore All S3 Actions

```bash
aws-ref s3
```

### Search for Specific Action

```bash
aws-ref s3 -a PutObject
```

### Verbose Mode (Show All Condition Keys)

```bash
aws-ref s3 -a PutObject -v
```

### Generate Example IAM Policy

```bash
aws-ref s3 -a PutObject --policy
```

## Usage Examples

### Example 1: Check Tag Support for S3 PutObject

```bash
$ aws-ref s3 -a PutObject

================================================================================
Action: PutObject
================================================================================

Properties:
  • Is Write:       ✓ Yes
  • Is Read:        ✗ No
  • Is List:        ✗ No
  • Is Tagging:     ✗ No
  • Is Permission:  ✗ No

Resource Types: 2
  • accesspointobject
  • object

Condition Key Support:
  Total Keys: 21

  Tag-Based Conditions:
    • RequestTag/*:  ✓ Supported (2 keys)
    • ResourceTag/*: ✗ Not Supported
    • TagKeys:       ✓ Supported

  ARN-Based Conditions:
    • Source ARN:    ✗ Not Supported
    • Source Acct:   ✗ Not Supported

  Other Condition Keys (19):
    (use -v to see all 19 keys)
```

### Example 2: Generate Policy with Condition Keys

```bash
$ aws-ref s3 -a PutObject --policy

Example IAM Policy:

Service: s3
Action: PutObject

Supported Resource Types:
  • accesspointobject
  • object

Policy JSON:
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:PutObject",
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestTag/Environment": "production"
        },
        "ForAllValues:StringEquals": {
          "aws:TagKeys": [
            "Environment",
            "Owner"
          ]
        }
      }
    }
  ]
}
```

### Example 3: Search Multiple Actions

```bash
aws-ref ec2 -a Describe
```

This will show all EC2 actions containing "Describe" in their name.

### Example 4: Check Lambda Function Tagging

```bash
aws-ref lambda -a TagResource -v
```

## Output Information

For each action, the tool displays:

### Properties
- **Is Write**: Whether the action modifies resources
- **Is Read**: Whether the action only reads data
- **Is List**: Whether the action lists resources
- **Is Tagging**: Whether the action is tagging-only
- **Is Permission**: Whether the action manages permissions

### Tag-Based Conditions
- **RequestTag/***: Conditions on tags in the request (e.g., during resource creation)
- **ResourceTag/***: Conditions on existing resource tags
- **TagKeys**: Conditions on which tag keys are present

### ARN-Based Conditions
- **Source ARN**: Whether action supports source ARN conditions
- **Source Account**: Whether action supports source account conditions

### Other Information
- **Resource Types**: What resource types the action can operate on
- **All Condition Keys**: Complete list of supported condition keys (with `-v`)
- **IAM Support**: Whether supported by IAM Access Analyzer and Action Last Accessed

## Common Use Cases

### Writing CloudFormation IAM Policies

```bash
# Check what condition keys are available for your action
aws-ref dynamodb -a PutItem -v

# Generate a policy template
aws-ref dynamodb -a PutItem --policy
```

### Debugging "Invalid Condition Key" Errors

```bash
# Verify if a condition key is actually supported
aws-ref s3 -a GetObject -v | grep -i "source"
```

### Understanding Tag-Based Access Control

```bash
# See which actions support tag conditions
aws-ref ec2 -a CreateInstance -v
```

### Exploring Service Permissions

```bash
# List all available services
aws-ref --list

# Explore a specific service
aws-ref secretsmanager
```

## Command-Line Options

```
usage: aws-ref [-h] [-a ACTION] [-v] [-l] [-p] [--no-color] [service]

AWS IAM Explorer - Explore IAM actions and their condition key support

positional arguments:
  service               AWS service name (e.g., s3, ec2, lambda)

optional arguments:
  -h, --help            show this help message and exit
  -a ACTION, --action ACTION
                        Filter by action name (supports partial matching)
  -v, --verbose         Show all condition keys in detail
  -l, --list            List all available AWS services
  -p, --policy          Generate example IAM policy for the action
  --no-color            Disable colored output
```

## Data Source

This tool uses the official AWS Service Authorization Reference API:
- Base URL: `https://servicereference.us-east-1.amazonaws.com/`
- Always up-to-date with the latest AWS services and actions
- No AWS credentials required!



## Acknowledgments

- AWS Service Authorization Reference for providing the data API
- All AWS Cloud Engineers struggling with IAM policies (I feel your pain! : D)
