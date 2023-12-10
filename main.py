from flask import Flask,jsonify,request
import boto3
import base64
import rsa
from dotenv import load_dotenv
import os

load_dotenv()

def decrypt_password_data(password_data, pk_path):
    encrypted_password = password_data['PasswordData']
    with open(pk_path) as pk_file:
        pk_contents = pk_file.read()
    private_key = rsa.PrivateKey.load_pkcs1(pk_contents.encode('latin-1'))
    value = base64.b64decode(encrypted_password)
    value = rsa.decrypt(value, private_key)
    decrypted_password = value.decode('utf-8')
    return decrypted_password

# AWS credentials
aws_access_key_id = os.environ.get('aws_access_key_id')
aws_secret_access_key = os.environ.get('aws_secret_access_key')
region_name = os.environ.get('region_name')

# EC2 instance parameters
instance_type = 't2.micro'
key_name = os.environ.get('key_name')
ami_id = 'ami-0cd601a22ac9e6d79'
subnet_id = os.environ.get('subnet_id')
security_group_ids=[os.environ.get('security_group_id')]

ec2 = boto3.client('ec2', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=region_name)

app = Flask(__name__)

@app.route('/start_lab')
def create_instance():

    response = ec2.run_instances(
        ImageId=ami_id,
        InstanceType=instance_type,
        KeyName=key_name,
        SecurityGroupIds=security_group_ids,
        SubnetId=subnet_id,
        MinCount=1,
        MaxCount=1
    )

    # Extract the instance ID
    instance_id = response['Instances'][0]['InstanceId']

    # Wait for the instance to be in the 'running' state
    ec2.get_waiter('instance_running').wait(InstanceIds=[instance_id])

    password_data = ec2.get_password_data(
        InstanceId=instance_id,  # Replace as needed
        DryRun=False
    )
    # Get public DNS of the instance
    response = ec2.describe_instances(InstanceIds=[instance_id])
    public_dns = response['Reservations'][0]['Instances'][0]['PublicDnsName']
    password = decrypt_password_data(password_data, 'wind-api.pem')

    return jsonify({'lab_id':instance_id,'full_address':public_dns,'password':password})

@app.route('/stop_lab')
def stop_instance():
    id = request.args.get('lab_id')
    response = ec2.stop_instances(InstanceIds=[id])
    # print(response['StoppingInstances'][0]['CurrentState']['Name'])
    return jsonify({'state':response['StoppingInstances'][0]['CurrentState']['Name']})

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000)