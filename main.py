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
ami_id = 'ami-0cd601a22ac9e6d79'

key_name = os.environ.get('key_name')
subnet_id = os.environ.get('subnet_id')
security_group_ids=[os.environ.get('security_group_id')]

# Creating the ec2 client 
ec2 = boto3.client('ec2', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=region_name)

# Flask app
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

    return jsonify({'lab_id':instance_id})

@app.route('/stop_lab')
def stop_instance():
    # Get instance id from the query parameter
    inst_id = request.args.get('lab_id')

    response = ec2.describe_instance_status(InstanceIds=[inst_id,],IncludeAllInstances=True)
    if(response['InstanceStatuses'][0]['InstanceState']['Name'] == 'running'):
        response = ec2.terminate_instances(InstanceIds=[inst_id])
        # print(response['StoppingInstances'][0]['CurrentState']['Name'])
        return jsonify({'status':'success','state':response['TerminatingInstances'][0]['CurrentState']['Name']})
    
    return jsonify({'status':'fail'})

@app.route('/lab_state')
def check_instance_state():
    # Get instance id from the query parameter
    inst_id = request.args.get('lab_id')

    # Describe the status of the EC2 instance
    response = ec2.describe_instance_status(InstanceIds=[inst_id,],IncludeAllInstances=True)
    
    return jsonify({'state':response['InstanceStatuses'][0]['InstanceState']['Name']})

@app.route('/lab_cred')
def get_instance_detail():
    # Get instance id from the query parameter
    inst_id = request.args.get('lab_id')

    response = ec2.describe_instance_status(InstanceIds=[inst_id,],IncludeAllInstances=True)
    print(response['InstanceStatuses'][0]['InstanceState']['Name'])
    if(response['InstanceStatuses'][0]['InstanceState']['Name'] == 'running'):
        # Get base64 password
        password_data = ec2.get_password_data(
            InstanceId=inst_id,
            DryRun=False
        )
        password = decrypt_password_data(password_data, 'wind-api.pem')
        response = ec2.describe_instances(InstanceIds=[inst_id])

        # Get public DNS of the instance
        public_dns = response['Reservations'][0]['Instances'][0]['PublicDnsName']

        return jsonify({'status':'success','full_addr':public_dns,'password':password})
    
    return jsonify({'status':'fail'})

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000)