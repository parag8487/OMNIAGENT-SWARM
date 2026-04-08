#!/bin/bash

# OmniAgent Swarm - Google Cloud Run Deployment Script
# Usage: ./deploy_gcp.sh [SERVICE_NAME] [REGION]

# Default values
SERVICE_NAME=${1:-"omniagent-swarm"}
REGION=${2:-"us-central1"}
IMAGE_NAME="omniagent-swarm"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}   OmniAgent Swarm - GCP Cloud Run Deployment    ${NC}"
echo -e "${BLUE}==================================================${NC}"

# 1. Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI not found. Please install it first.${NC}"
    exit 1
fi

# 2. Get current project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: No active GCP project. Run 'gcloud config set project [PROJECT_ID]'.${NC}"
    exit 1
fi

echo -e "${GREEN}Project ID: ${PROJECT_ID}${NC}"
echo -e "${GREEN}Service Name: ${SERVICE_NAME}${NC}"
echo -e "${GREEN}Region: ${REGION}${NC}"

# 3. Enable necessary APIs
echo -e "\n${YELLOW}Enabling necessary APIs...${NC}"
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com

# 4. Create Artifact Registry if it doesn't exist
REPO_NAME="omniagent-repo"
echo -e "\n${YELLOW}Ensuring Artifact Registry repository exists...${NC}"
RES=$(gcloud artifacts repositories describe $REPO_NAME --location=$REGION 2>&1)
if [[ $RES == *"NOT_FOUND"* ]]; then
    gcloud artifacts repositories create $REPO_NAME \
        --repository-format=docker \
        --location=$REGION \
        --description="OmniAgent Swarm Docker Repository"
fi

IMAGE_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}"

# 5. Build and Push using Cloud Build
echo -e "\n${YELLOW}Building and pushing container image via Cloud Build...${NC}"
gcloud builds submit --tag "$IMAGE_URL" .

# 6. Extract Env Vars from .env for deployment
# Only include keys that are defined in .env.template
echo -e "\n${YELLOW}Preparing environment variables...${NC}"
ENV_VARS=""
if [ -f .env ]; then
    # Read .env and format for gcloud --set-env-vars
    while IFS='=' read -r key value || [ -n "$key" ]; do
        # Ignore comments and empty lines
        if [[ ! "$key" =~ ^# ]] && [[ -n "$key" ]]; then
            # Clean up value (remove quotes)
            clean_value=$(echo "$value" | sed "s/['\"]//g")
            if [ -z "$ENV_VARS" ]; then
                ENV_VARS="${key}=${clean_value}"
            else
                ENV_VARS="${ENV_VARS},${key}=${clean_value}"
            fi
        fi
    done < .env
else
    echo -e "${YELLOW}Warning: .env file not found. Deployment will proceed without custom environment variables.${NC}"
fi

# 7. Deploy to Cloud Run
echo -e "\n${YELLOW}Deploying to Cloud Run...${NC}"
if [ -n "$ENV_VARS" ]; then
    gcloud run deploy "$SERVICE_NAME" \
        --image "$IMAGE_URL" \
        --region "$REGION" \
        --platform managed \
        --allow-unauthenticated \
        --set-env-vars "$ENV_VARS" \
        --memory 2Gi \
        --cpu 2 \
        --timeout 3600
else
    gcloud run deploy "$SERVICE_NAME" \
        --image "$IMAGE_URL" \
        --region "$REGION" \
        --platform managed \
        --allow-unauthenticated \
        --memory 2Gi \
        --cpu 2 \
        --timeout 3600
fi

echo -e "\n${GREEN}==================================================${NC}"
echo -e "${GREEN}   Deployment Complete!${NC}"
echo -e "${GREEN}   Service URL can be found above.${NC}"
echo -e "${GREEN}==================================================${NC}"
