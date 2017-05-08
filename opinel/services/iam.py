# -*- coding: utf-8 -*-

def get_aws_account_id(iam_client):
    try:
        user_arn = iam_client.list_users(MaxItems = 1)['Users'][0]['Arn']
    except:
        user_arn = iam_client.get_user()['User']['Arn']
    return user_arn.split(':')[4]
