# TODO: edit these
PROJECT_ID="hybrid-vertex"
PROJECT_NUM="934903580331"
LOCATION="us-central1"
VERSION= "v1"
PREFIX=f"vertex-forecast-{VERSION}"
VPC_NETWORK_NAME="ucaip-haystack-vpc-network"
# Leave these
BUCKET_NAME=f"{PREFIX}-{PROJECT_ID}"
BUCKET_URI=f"gs://{BUCKET_NAME}"
VPC_NETWORK_FULL=f"projects/{PROJECT_NUM}/global/networks/{VPC_NETWORK_NAME}"
VERTEX_SA=f"{PROJECT_NUM}-compute@developer.gserviceaccount.com"