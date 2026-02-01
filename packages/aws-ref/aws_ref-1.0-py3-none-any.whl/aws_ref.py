#!/usr/bin/env python3

import argparse
import json
import re
import ssl
import sys
from typing import Dict, List, Optional
from urllib.request import urlopen
from urllib.error import URLError

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @classmethod
    def disable(cls):
        cls.HEADER = ''
        cls.OKBLUE = ''
        cls.OKCYAN = ''
        cls.OKGREEN = ''
        cls.WARNING = ''
        cls.FAIL = ''
        cls.ENDC = ''
        cls.BOLD = ''
        cls.UNDERLINE = ''


class AWSIAMExplorer:

    BASE_URL = "https://servicereference.us-east-1.amazonaws.com"

    def __init__(self):
        self.services = {}
        self.ssl_context = ssl._create_unverified_context()
    def fetch_services_list(self) -> List[Dict]:
        try:
            with urlopen(f"{self.BASE_URL}/", context=self.ssl_context) as response:
                return json.loads(response.read().decode('utf-8'))
        except URLError as e:
            print(f"{Colors.FAIL}Error fetching services list: {e}{Colors.ENDC}")
            sys.exit(1)
    
    def fetch_service_data(self, service_name: str) -> Optional[Dict]:
        services = self.fetch_services_list()

        service_url = None
        for svc in services:
            if svc['service'].lower() == service_name.lower():
                service_url = svc['url']
                break
        
        if not service_url:
            return None
        
        try:
            with urlopen(service_url, context=self.ssl_context) as response:
                return json.loads(response.read().decode('utf-8'))
        except URLError as e:
            print(f"{Colors.FAIL}Error fetching service data: {e}{Colors.ENDC}")
            return None
    
    def categorize_condition_keys(self, condition_keys: List[str]) -> Dict:
        categories = {
            'aws_request_tag': [],      # aws:RequestTag/${TagKey}
            'aws_resource_tag': [],     # aws:ResourceTag/${TagKey}
            'aws_tag_keys': [],         # aws:TagKeys
            'service_request_tag': [],  # service:RequestObjectTag/<key>, etc.
            'service_resource_tag': [], # service:ExistingObjectTag/<key>, etc.
            'service_tag_keys': [],     # service:RequestObjectTagKeys, etc.
            'source_arn': [],           # *SourceArn*
            'source_account': [],       # *SourceAccount*
            'other': []
        }
        for key in condition_keys:
            key_lower = key.lower()
            if key == 'aws:RequestTag/${TagKey}':
                categories['aws_request_tag'].append(key)
            elif key == 'aws:ResourceTag/${TagKey}':
                categories['aws_resource_tag'].append(key)
            elif key == 'aws:TagKeys':
                categories['aws_tag_keys'].append(key)
            elif 'requesttag' in key_lower or 'request-tag' in key_lower:
                categories['service_request_tag'].append(key)
            elif 'resourcetag' in key_lower or 'existingtag' in key_lower or 'existing' in key_lower and 'tag' in key_lower:
                categories['service_resource_tag'].append(key)
            elif 'tagkeys' in key_lower or 'tag-keys' in key_lower:
                categories['service_tag_keys'].append(key)
            elif 'sourcearn' in key_lower or 'source-arn' in key_lower:
                categories['source_arn'].append(key)
            elif 'sourceaccount' in key_lower or 'source-account' in key_lower:
                categories['source_account'].append(key)
            else:
                categories['other'].append(key)

        return categories

    def display_action_details(self, action: Dict, verbose: bool = False):
        action_name = action.get('Name', 'Unknown')
        service_name = self.current_service if hasattr(self, 'current_service') else ''
        full_action = f"{service_name}:{action_name}" if service_name else action_name
        print(f"\n{Colors.BOLD}{Colors.OKCYAN}{'='*80}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}Action: {full_action}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.OKCYAN}{'='*80}{Colors.ENDC}\n")

        annotations = action.get('Annotations', {}).get('Properties', {})
        print(f"{Colors.BOLD}Properties:{Colors.ENDC}")
        print(f"  • Is Write:       {self._format_bool(annotations.get('IsWrite', False))}")
        print(f"  • Is Read:        {self._format_bool(not annotations.get('IsWrite', False))}")
        print(f"  • Is List:        {self._format_bool(annotations.get('IsList', False))}")
        print(f"  • Is Tagging:     {self._format_bool(annotations.get('IsTaggingOnly', False))}")
        print(f"  • Is Permission:  {self._format_bool(annotations.get('IsPermissionManagement', False))}")

        resources = action.get('Resources', [])
        print(f"\n{Colors.BOLD}Resource Types: {Colors.OKGREEN}{len(resources)}{Colors.ENDC}")
        if resources:
            for resource in resources:
                resource_name = resource.get('Name', 'unknown')
                print(f"  • {resource_name}")
        else:
            print(f"  {Colors.WARNING}No specific resource types{Colors.ENDC}")

        condition_keys = action.get('ActionConditionKeys', [])
        categories = self.categorize_condition_keys(condition_keys)

        print(f"\n{Colors.BOLD}Condition Keys ({len(condition_keys)} total):{Colors.ENDC}")
        has_aws_tags = any([categories['aws_request_tag'], categories['aws_resource_tag'], categories['aws_tag_keys']])
        if has_aws_tags or verbose:
            print(f"\n{Colors.BOLD}  AWS Global Tag Conditions:{Colors.ENDC}")
            print(f"    • aws:RequestTag/${{TagKey}}:  {self._format_support(categories['aws_request_tag'])}")
            print(f"    • aws:ResourceTag/${{TagKey}}: {self._format_support(categories['aws_resource_tag'])}")
            print(f"    • aws:TagKeys:                 {self._format_support(categories['aws_tag_keys'])}")

        has_service_tags = any([categories['service_request_tag'], categories['service_resource_tag'], categories['service_tag_keys']])
        if has_service_tags:
            print(f"\n{Colors.BOLD}  Service-Specific Tag Conditions:{Colors.ENDC}")
            if categories['service_request_tag']:
                print(f"    • Request Tags: {Colors.OKGREEN}✓ Supported{Colors.ENDC}")
                if verbose:
                    for key in categories['service_request_tag']:
                        print(f"        - {key}")
            else:
                print(f"    • Request Tags: {Colors.FAIL}✗ Not Supported{Colors.ENDC}")
            
            if categories['service_resource_tag']:
                print(f"    • Resource Tags: {Colors.OKGREEN}✓ Supported{Colors.ENDC}")
                if verbose:
                    for key in categories['service_resource_tag']:
                        print(f"        - {key}")
            else:
                print(f"    • Resource Tags: {Colors.FAIL}✗ Not Supported{Colors.ENDC}")
            
            if categories['service_tag_keys']:
                print(f"    • Tag Keys: {Colors.OKGREEN}✓ Supported{Colors.ENDC}")
                if verbose:
                    for key in categories['service_tag_keys']:
                        print(f"        - {key}")
            else:
                print(f"    • Tag Keys: {Colors.FAIL}✗ Not Supported{Colors.ENDC}")
        
        has_arn_conditions = any([categories['source_arn'], categories['source_account']])
        if has_arn_conditions or verbose:
            print(f"\n{Colors.BOLD}  ARN-Based Conditions:{Colors.ENDC}")
            print(f"    • Source ARN:     {self._format_support(categories['source_arn'])}")
            if verbose and categories['source_arn']:
                for key in categories['source_arn']:
                    print(f"        - {key}")
            
            print(f"    • Source Account: {self._format_support(categories['source_account'])}")
            if verbose and categories['source_account']:
                for key in categories['source_account']:
                    print(f"        - {key}")

        if categories['other']:
            print(f"\n{Colors.BOLD}  Other Condition Keys ({len(categories['other'])}):{Colors.ENDC}")
            if verbose:
                for key in categories['other']:
                    print(f"    • {key}")
            else:
                print(f"    {Colors.WARNING}(use -v to see all {len(categories['other'])} keys){Colors.ENDC}")

        supported = action.get('SupportedBy', {})
        print(f"\n{Colors.BOLD}Supported By:{Colors.ENDC}")
        print(f"  • IAM Access Analyzer:  {self._format_bool(supported.get('IAM Access Analyzer Policy Generation', False))}")
        print(f"  • Action Last Accessed: {self._format_bool(supported.get('IAM Action Last Accessed', False))}")

        service_name = self.current_service if hasattr(self, 'current_service') else 's3'
        print(f"\n{Colors.BOLD}Documentation:{Colors.ENDC}")
        print(f"  https://docs.aws.amazon.com/service-authorization/latest/reference/list_{service_name.replace('-', '')}.html")

    def _format_bool(self, value: bool) -> str:
        if value:
            return f"{Colors.OKGREEN}✓ Yes{Colors.ENDC}"
        return f"{Colors.FAIL}✗ No{Colors.ENDC}"

    def _format_support(self, value) -> str:
        if isinstance(value, bool):
            return f"{Colors.OKGREEN}✓ Supported{Colors.ENDC}" if value else f"{Colors.FAIL}✗ Not Supported{Colors.ENDC}"
        elif isinstance(value, list):
            if len(value) > 0:
                return f"{Colors.OKGREEN}✓ Supported{Colors.ENDC}"
            return f"{Colors.FAIL}✗ Not Supported{Colors.ENDC}"
        return f"{Colors.WARNING}? Unknown{Colors.ENDC}"

    def search_actions(self, service_name: str, action_filter: Optional[str] = None, verbose: bool = False):
        print(f"\n{Colors.BOLD}{Colors.HEADER}Fetching IAM data for service: {service_name}...{Colors.ENDC}")
        
        self.current_service = service_name  # Store for documentation links
        service_data = self.fetch_service_data(service_name)
        
        if not service_data:
            print(f"{Colors.FAIL}Service '{service_name}' not found!{Colors.ENDC}")
            print(f"\n{Colors.WARNING}Tip: Use --list to see all available services{Colors.ENDC}")
            sys.exit(1)
        
        actions = service_data.get('Actions', [])
        
        if action_filter:
            filtered_actions = [
                a for a in actions 
                if action_filter.lower() in a.get('Name', '').lower()
            ]
            if not filtered_actions:
                print(f"{Colors.FAIL}No actions matching '{action_filter}' found!{Colors.ENDC}")
                sys.exit(1)
            actions = filtered_actions
        
        print(f"{Colors.OKGREEN}Found {len(actions)} action(s){Colors.ENDC}\n")
        
        for action in actions:
            self.display_action_details(action, verbose)
    
    def list_services(self):
        services = self.fetch_services_list()
        print(f"\n{Colors.BOLD}{Colors.HEADER}Available AWS Services ({len(services)}):{Colors.ENDC}\n")
        grouped = {}
        for svc in services:
            name = svc['service']
            first_char = name[0].upper()
            if first_char not in grouped:
                grouped[first_char] = []
            grouped[first_char].append(name)
        
        for letter in sorted(grouped.keys()):
            print(f"{Colors.BOLD}{Colors.OKCYAN}{letter}{Colors.ENDC}")
            for name in sorted(grouped[letter]):
                print(f"  • {name}")
            print()
    
    def generate_policy_example(self, service_name: str, action_name: str):
        service_data = self.fetch_service_data(service_name)
        
        if not service_data:
            print(f"{Colors.FAIL}Service '{service_name}' not found!{Colors.ENDC}")
            sys.exit(1)
        
        action = None
        for a in service_data.get('Actions', []):
            if a.get('Name', '').lower() == action_name.lower():
                action = a
                break
        
        if not action:
            print(f"{Colors.FAIL}Action '{action_name}' not found in service '{service_name}'!{Colors.ENDC}")
            sys.exit(1)
        
        condition_keys = action.get('ActionConditionKeys', [])
        categories = self.categorize_condition_keys(condition_keys)
        resources = action.get('Resources', [])
        
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": f"{service_name}:{action_name}",
                    "Resource": "*"
                }
            ]
        }
        
        conditions = {}
        
        if categories['aws_request_tag']:
            conditions['StringEquals'] = conditions.get('StringEquals', {})
            conditions['StringEquals']['aws:RequestTag/Environment'] = 'production'
        elif categories['service_request_tag']:
            conditions['StringEquals'] = conditions.get('StringEquals', {})
            example_key = categories['service_request_tag'][0]
            conditions['StringEquals'][example_key] = 'production'
        
        if categories['aws_resource_tag']:
            conditions['StringEquals'] = conditions.get('StringEquals', {})
            conditions['StringEquals']['aws:ResourceTag/Owner'] = '${aws:username}'
        elif categories['service_resource_tag']:
            conditions['StringEquals'] = conditions.get('StringEquals', {})
            example_key = categories['service_resource_tag'][0]
            conditions['StringEquals'][example_key] = '${aws:username}'
        
        if categories['aws_tag_keys']:
            conditions['ForAllValues:StringEquals'] = conditions.get('ForAllValues:StringEquals', {})
            conditions['ForAllValues:StringEquals']['aws:TagKeys'] = ['Environment', 'Owner']
        elif categories['service_tag_keys']:
            conditions['ForAllValues:StringEquals'] = conditions.get('ForAllValues:StringEquals', {})
            example_key = categories['service_tag_keys'][0]
            conditions['ForAllValues:StringEquals'][example_key] = ['Environment', 'Owner']
        
        if categories['source_arn']:
            conditions['ArnEquals'] = conditions.get('ArnEquals', {})
            example_key = categories['source_arn'][0]
            conditions['ArnEquals'][example_key] = 'arn:aws:service:region:account:resource/*'
        
        if conditions:
            policy['Statement'][0]['Condition'] = conditions
        
        print(f"\n{Colors.BOLD}{Colors.HEADER}Example IAM Policy:{Colors.ENDC}\n")
        print(f"{Colors.BOLD}Service:{Colors.ENDC} {service_name}")
        print(f"{Colors.BOLD}Action:{Colors.ENDC} {action_name}")
        
        if resources:
            print(f"\n{Colors.BOLD}Supported Resource Types:{Colors.ENDC}")
            for res in resources:
                print(f"  • {res.get('Name', 'unknown')}")
        
        print(f"\n{Colors.BOLD}Policy JSON:{Colors.ENDC}")
        print(json.dumps(policy, indent=2))
        
        if conditions:
            print(f"\n{Colors.WARNING}Note: This is an example with supported condition keys.{Colors.ENDC}")
            print(f"{Colors.WARNING}Adjust the condition values based on your specific requirements.{Colors.ENDC}")


def main():
    parser = argparse.ArgumentParser(
        description='aws-ref : Explore IAM actions and their condition key support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all available AWS services
  %(prog)s --list
  
  # Show all S3 actions
  %(prog)s s3
  
  # Show specific S3 action with verbose output
  %(prog)s s3 -a PutObject -v
  
  # Search for actions containing "Put"
  %(prog)s s3 -a Put
  
  # Generate example policy
  %(prog)s s3 -a PutObject --policy
  
  # Disable colors (for piping to files)
  %(prog)s s3 --no-color > output.txt

Data Source:
  AWS Service Authorization Reference API
  https://servicereference.us-east-1.amazonaws.com/
  https://docs.aws.amazon.com/service-authorization/latest/reference/
        """
    )
    
    parser.add_argument(
        'service',
        nargs='?',
        help='AWS service name (e.g., s3, ec2, lambda)'
    )
    
    parser.add_argument(
        '-a', '--action',
        help='Filter by action name (supports partial matching)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show all condition keys in detail'
    )
    
    parser.add_argument(
        '-l', '--list',
        action='store_true',
        help='List all available AWS services'
    )
    
    parser.add_argument(
        '-p', '--policy',
        action='store_true',
        help='Generate example IAM policy for the action'
    )
    
    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output'
    )
    
    args = parser.parse_args()
    
    if args.no_color or not sys.stdout.isatty():
        Colors.disable()
    
    explorer = AWSIAMExplorer()
    
    try:
        if args.list:
            explorer.list_services()
        elif args.policy:
            if not args.service or not args.action:
                print(f"{Colors.FAIL}Error: --policy requires both service and action{Colors.ENDC}")
                sys.exit(1)
            explorer.generate_policy_example(args.service, args.action)
        elif args.service:
            explorer.search_actions(args.service, args.action, args.verbose)
        else:
            parser.print_help()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Interrupted by user{Colors.ENDC}")
        sys.exit(0)


if __name__ == '__main__':
    main()
