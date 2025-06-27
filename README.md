# ai-sandbox
Here are the prerequisites for this project:
0. Create a GCP project if you do not have one (console.cloud.google.com), enable vertex ai rag engine. (free credits should be available in case you have not used them up)
1. Create a account and a cluster on Weaviate Cloud (this is currently free for a trial period) https://console.weaviate.cloud/
2. Get the Weaviate API keys from the console (https://console.weaviate.cloud) for the cluster you created and store the key in the GCP project's (created in step 0) Secret Manager.
   Provide a friendly name such as `weaviate_key` to identify the resource
   a. Get the URL of this resource you created (along with the version) - will be of the format "projects/<project id>/secrets/weaviate_key/versions/1"  - this will be used to set an environment variable later on
3. Provide the GCP RAG Engine service account permissions to access the secret manager:
   a. Navigate to https://console.cloud.google.com/iam-admin/iam
   b. Select the option "Include Google-provided role grants" on the top left
   c. Find the service account, which has the format service-{project number}@gcp-sa-vertex-rag.iam.gserviceaccount.com 
   d. Edit the service account's principals.
   e. Add the Secret Manager Secret Accessor role (secretmanager.versions.access) to the service account.
   
4. python3 -m venv .venv
5. source .venv/bin/activate
6. pip3 install vertexai
7. pip3 install -U weaviate-client
8. pip3 install -U pandas python-dotenv streamlit
9. Set the following environment variables :
   export PROJECT_ID = <your GCP project ID>
   export LOCATION = <your GCP cloud region> # if you leave this empty by default the us-central1 region will be used
   export WEAVIATE_HTTP_ENDPOINT = <your weaviate cluster endpoint>
   export WEAVIATE_API_KEY = <your weaviate api key>
   export VERTEX_API_KEY = <your vertex api key>
   export SM_WEAVIATE_API_KEY_RESOURCE = <your GCP secret manager location where you stored the weaviate key> # from step 2(a) above
   
   
