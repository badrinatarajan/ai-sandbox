import weaviate
from weaviate.classes.init import Auth
from weaviate.client import WeaviateClient
import os

def connect_to_weaviate_cloud_db(weaviate_url, weaviate_key) -> WeaviateClient:

    # Recommended: save sensitive data as environment variables
    vertex_key = os.getenv("VERTEX_API_KEY")
    #studio_key = os.getenv("STUDIO_APIKEY")
    headers = {
        "X-Goog-Vertex-Api-Key": vertex_key,
    #    "X-Goog-Studio-Api-Key" : studio_key
    }

    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=weaviate_url,                       # `weaviate_url`: your Weaviate URL
        auth_credentials=Auth.api_key(weaviate_key),    # `weaviate_key`: your Weaviate API key
        headers=headers
    )

    return client


# def main():

#     client = connect_to_weaviate_cloud_db()  # Could also use this to connect to your own Weaviate instance

#     try:
#         # Check whether the client is ready
#         assert client.is_ready()  # Check connection status (i.e. is the Weaviate server ready)
#         print(f'client is ready: {client.is_ready()}')
#     finally:
#         # Close the connection
#         client.close()


# if __name__ == "__main__":
#     main()