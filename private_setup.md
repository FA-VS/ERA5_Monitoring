For the necessary installs, check the dockerfile and the requirements.txt

# MLflow server
Point to Neon database URI (obtain it from their web UI)
Must be done *every* time a server is started.
(note complaints about Registry store URI not provided, using backend instead)
```
$ source ~/.mlflow_env
$ source ~/.aws-s3_env # Optional
$ mlflow ui --backend-store-uri $MLFLOW_TRACKING_URI --default-artifact-root $MLFLOW_ARTIFACT_URI
```

~/.mlflow_env contains the following:
```
export MLFLOW_TRACKING_URI="postgresql://user:pass@your-neon-host/dbname"
export MLFLOW_ARTIFACT_URI="s3://my-mlflow-artifacts/"
```
This includes the username+password IN PLAIN TEXT of the Neon database, so make sure to chmod 600 the file, to limit the damage...
Alternatively, set this up with a keychain / secret manager.

~/.aws-s3_env (optional, only needed for debugging) contains the following:
```
export AWS_ACCESS_KEY="YOURKEY"
export AWS_SECRET_ACCESS_KEY="yOuRsEcReTkEy"
export AWS_DEFAULT_REGION="your-region"
```
This includes the public+secret key IN PLAIN TEXT of your AWS S3 account, so make sure to chmod 600 the file, to limit the damage...



# S3 bucket permissions
One-time setup

AWS Console -> S3 (fint it in search bar) -> Create (general purpose) bucket.
  - Choose a GLOBALLY UNIQUE name, and a region close to you
  - Note the bucket and region names.
  - Put the bucket name in MLFLow_Monitoring.py BEFORE you run for the first time!!!


IAM (find it in search bar) -> Policies -> Create policy -> JSON -> Paste the following (minimal) permissions:
```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::bucket-name"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::bucket-name/*"
    }
  ]
}
```
You can remove "PutObject" and "DeleteObject" for a read-only policy.


### Path 1: users (for interactive sessions)

IAM -> Users -> Create user -> ???

Attach (minimal) policy to this new user.

Security credentials -> Create access key -> "Application running outside AWS" -> ???
  - Note the Access Key ID and Secret Access Key - the Secret will only be shown ONCE!

In the machine you want to run from, do `aws configure`.
Give it the AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION (e.g. eu-north-1), keep format empty.
This will create the file ~/.aws/credentials.

### Path 2: roles (for github actions)

IAM -> Identity providers -> Add provider:
  - Open ID Connect
  - provider URL: https://token.actions.githubusercontent.com
  - audience: sts.amazonaws.com

IAM -> Roles -> Create Role -> Web identity:
  - Select github provider
  - github organization: my github username (e.g. FA-VS)
  - Add trust condition restricting it to specific repo (e.g. repo:FA-VS/ERA5-Monitoring:*
  - When done, note down the ARN for this role.

Attach (minimal) policy to this new web-identity role



# Github actions

For Neon database, you need MLFLOW_TRACKING_URI in your secrets (includes username and password).
In any github action job/step that will launch mlflow, make sure to add:
```
env:
  MLFLOW_TRACKING_URI: ${{ secrets.MLFLOW_TRACKING_URI }}
```
for any job that will launch mlflow.


For AWS S3, you need AWS_ROLE_ARN in your secrets (technically public information).
In any github action job that will launch mlflow, make sure to add:
```
permissions:
  contents: read    # Standard
  id-token: write   # Required to generate OIDC token
steps:
  - uses: aws-actions/configure-aws-credentials@v4 # Will set all the AWS envvars
    with:
      role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
      aws-region: your-aws-region (eg. eu-north-1)
```
This will load AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN, AWS_REGION and AWS_DEFAULT_REGION as environment variables.

