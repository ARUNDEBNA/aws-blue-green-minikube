# AWS Blue-Green Deployment with Minikube, Jenkins & GitHub Actions

This project automates the deployment of:
- A Minikube Kubernetes cluster on AWS EC2
- Jenkins running on Kubernetes
- A Node.js application with blue-green deployment
- All using a single Python script and GitHub Actions pipeline

## Features

- Builds and pushes Docker images to Amazon ECR
- Provisions an EC2 instance and installs Minikube
- Deploys blue and green versions of a Node.js app
- Jenkins is deployed to Kubernetes for future CI/CD use
- GitHub Actions triggers the whole pipeline on push
## Prerequisites

- AWS account
- IAM user with EC2, ECR, and EKS permissions
- GitHub repository with these secrets:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_ACCOUNT_ID`

## Usage

1. Clone this repository and push to your GitHub account.
2. Add required GitHub secrets.
3. Commit any change to trigger the workflow.
4. Watch GitHub Actions create your environment.

## File Structure

- `scripts/deploy.py`: Main automation script
- `node-app/`: Simple Node.js app to be deployed
- `jenkins/`: Kubernetes manifest for Jenkins
- `blue-green/`: K8s manifests for blue and green versions + service
- `.github/workflows/deploy.yml`: GitHub Actions workflow

## Traffic Switching

Default service directs to the **blue** version. You can manually run a patch command to switch:

```sh
kubectl patch service node-app-service -p '{"spec":{"selector":{"app":"node-app","version":"green"}}}'
```

## Cleanup

- Terminate EC2 instance from AWS Console
- Remove ECR repositories if no longer needed
