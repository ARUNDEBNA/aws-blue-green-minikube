import boto3
import paramiko
import os
import time
import subprocess

AWS_REGION = 'us-east-1'
AMI_ID = 'ami-0c02fb55956c7d316'
INSTANCE_TYPE = 't2.medium'
KEY_NAME = 'minikube-key'
SEC_GROUP = 'minikube-sg'
REPOS = ['node-app-blue', 'node-app-green']

def create_ecr_repo(ecr_client, name):
    try:
        ecr_client.create_repository(repositoryName=name)
        print(f"Created ECR repo: {name}")
    except ecr_client.exceptions.RepositoryAlreadyExistsException:
        print(f"ECR repo already exists: {name}")

def build_and_push_images(ecr_client, account_id):
    for repo in REPOS:
        image_uri = f'{522806196718}.dkr.ecr.{AWS_REGION}.amazonaws.com/{repo}:latest'
        print(f"Building image {image_uri}")
        subprocess.run(['docker', 'build', '-t', image_uri, './node-app'], check=True)
        subprocess.run(['docker', 'push', image_uri], check=True)

def launch_ec2():
    ec2 = boto3.resource('ec2', region_name=AWS_REGION)
    instance = ec2.create_instances(
        ImageId=AMI_ID,
        InstanceType=INSTANCE_TYPE,
        MinCount=1,
        MaxCount=1,
        KeyName=KEY_NAME,
        SecurityGroups=[SEC_GROUP]
    )[0]
    print("Launching EC2...")
    instance.wait_until_running()
    instance.reload()
    print(f"Instance IP: {instance.public_ip_address}")
    return instance.public_ip_address

def ssh_connect(ip):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    time.sleep(60)
    ssh.connect(ip, username='ec2-user', key_filename='minikube-key.pem')
    return ssh

def setup_minikube_and_k8s(ssh):
    cmds = [
        'sudo yum update -y',
        'sudo yum install -y docker wget conntrack git',
        'sudo service docker start',
        'sudo usermod -aG docker ec2-user',
        'curl -Lo minikube https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64',
        'chmod +x minikube',
        'sudo mv minikube /usr/local/bin/',
        'curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"',
        'chmod +x kubectl',
        'sudo mv kubectl /usr/local/bin/',
        'minikube start --driver=none'
    ]
    for cmd in cmds:
        print(f"> {cmd}")
        ssh.exec_command(cmd)

def deploy_k8s_apps(ssh):
    yaml_files = ['jenkins-deployment.yaml', 'app-blue.yaml', 'app-green.yaml', 'service.yaml']
    sftp = ssh.open_sftp()
    for file in yaml_files:
        local_path = f'./blue-green/{file}' if 'app' in file or 'service' in file else f'./jenkins/{file}'
        sftp.put(local_path, f'/home/ec2-user/{file}')
    sftp.close()

    for file in yaml_files:
        ssh.exec_command(f'kubectl apply -f {file}')

def switch_traffic_to(version, ssh):
    update = f"kubectl patch service node-app-service -p '{{\"spec\":{{\"selector\":{{\"app\":\"node-app\",\"version\":\"{version}\"}}}}}}'"
    print(f"Switching traffic to {version}")
    ssh.exec_command(update)

def main():
    boto_session = boto3.session.Session(region_name=AWS_REGION)
    ecr = boto_session.client('ecr')
    sts = boto_session.client('sts')
    account_id = sts.get_caller_identity()['Account']

    for repo in REPOS:
        create_ecr_repo(ecr, repo)

    subprocess.run(['aws', 'ecr', 'get-login-password', '--region', AWS_REGION], check=True, stdout=subprocess.PIPE)

    build_and_push_images(ecr, account_id)

    ec2_ip = launch_ec2()
    ssh = ssh_connect(ec2_ip)
    setup_minikube_and_k8s(ssh)
    deploy_k8s_apps(ssh)

    switch_traffic_to("blue", ssh)
    ssh.close()

if __name__ == "__main__":
    main()