import json
import boto3
import csv
import os
from urllib import unquote_plus

s3=boto3.client('s3')
client = boto3.client('quicksight')
account_number='111122223333'
namespace='default'

def get_existing_groups():
    existing_groups=[]

    response = client.list_groups(
    AwsAccountId=account_number,
    Namespace=namespace)

    for i in range (len(response['GroupList'])):
        existing_groups.append(response['GroupList'][i]['GroupName'].encode('utf-8')) 
    return existing_groups


def get_file_contents(bucket,key):

    resp=s3.get_object(Bucket=bucket,Key=key)
    lines = resp['Body'].read().split()
    input_file = csv.DictReader(lines)
    return input_file

def create_quick_sight_groups_bulk(bucket,key):

    existing_groups=get_existing_groups()
    input_file = get_file_contents(bucket,key)
    for row in input_file:
        row=row['Group'].replace(' ','_')
        if row not in existing_groups:
            row=row.replace(' ','_')
            create_quick_sight_group(row)
            existing_groups.append(row)

def create_quick_sight_group(group_name):

    response = client.create_group(
        GroupName=group_name,
        Description='Group:'+group_name,
        AwsAccountId=account_number,
        Namespace=namespace)

def add_user_to_group(user_name,group_name):
    response = client.create_group_membership(
        MemberName=user_name,
        GroupName=group_name,
        AwsAccountId=account_number,
        Namespace=namespace)

def create_user_group_memebership_bulk(bucket,key):

    existing_groups=get_existing_groups()
    input_file = get_file_contents(bucket,key) 
    for row in input_file:
        if " " in row['Group'].replace(' ','_'):
            grp=row['Group'].replace(' ','_')
        else: 
            grp=row['Group']
        usr=row['User']
        if grp not in existing_groups:
            create_quick_sight_group(grp)
            existing_groups.append(grp)
            add_user_to_group(usr,grp)

def remove_user_membership(user,group):

    response = client.delete_group_membership(
        MemberName=user,
        GroupName=group,
        AwsAccountId=account_number,
        Namespace=namespace)

def remove_users_from_group(bucket,key):

    input_file = get_file_contents(bucket,key) 
    for row in input_file:
        grp=row['Group']
        usr=row['User']
        remove_user_membership(usr,grp)


def lambda_handler(event, context): 

    print(event)
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    file_key = str(unquote_plus(event['Records'][0]['s3']['object']['key']))
    if 'add-user-to-group' in file_key:
        create_user_group_memebership_bulk(bucket_name,file_key)
    elif 'remove-user-from-group' in file_key:
        remove_users_from_group(bucket_name,file_key)
    elif 'add-groups' in file_key:
        create_quick_sight_groups_bulk(bucket_name,file_key)
