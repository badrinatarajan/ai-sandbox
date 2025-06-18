import weaviate.classes.config as wc
import weaviate
import utils
import vertexai
import os
import sys
from vertexai.preview import rag
from vertexai.preview.generative_models import GenerativeModel, Tool

from weaviate.classes.config import Configure

PROJECT_ID = str(os.environ.get("GOOGLE_CLOUD_PROJECT"))
LOCATION = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")
WEAVIATE_HTTP_ENDPOINT=str(os.environ.get("WEAVIATE_HTTP_ENDPOINT"))
WEAVIATE_API_KEY= str(os.environ.get("WEAVIATE_API_KEY"))
VERTEX_API_KEY= str(os.environ.get("VERTEX_API_KEY"))
SM_WEAVIATE_API_KEY_RESOURCE = str(os.environ.get("SM_WEAVIATE_API_KEY_RESOURCE"))
COLLECTION_NAME = "WikiDataCollection"
RAG_CORPUS_DISPLAY_NAME="WikiDataCollectionCorpus"
DATA_DIR="./data"
DATA_FILE = "chunks.json"

    
    



def connect_and_get_client():
    client =  utils.connect_to_weaviate_cloud_db(WEAVIATE_HTTP_ENDPOINT, WEAVIATE_API_KEY)  # Connect to our own database
    return client

def create_collection(client):

    if client.collections.exists(COLLECTION_NAME):
        print(f'Using existing collection {COLLECTION_NAME} ...')
        collection = client.collections.get(COLLECTION_NAME)

    else:     
        try :
            print(f'Creating new collection {COLLECTION_NAME}...')
            client.collections.create(
            name=COLLECTION_NAME,
            properties=[
                wc.Property(name="fileId", data_type=wc.DataType.TEXT),
                wc.Property(name="corpusId", data_type=wc.DataType.TEXT),
                wc.Property(name="chunkId", data_type=wc.DataType.TEXT),
                wc.Property(name="chunkDataType", data_type=wc.DataType.TEXT),
                wc.Property(name="chunkData", data_type=wc.DataType.TEXT),
                wc.Property(name="fileOriginalUri", data_type=wc.DataType.TEXT),
            ]
            )
            collection = client.collections.get(COLLECTION_NAME)
            print(f'Successfully created collection: {COLLECTION_NAME}')            
        except  weaviate.exceptions.WeaviateBaseError as e:
            return {
            "status": "error",
            "error_message": str(e),
            "message": f"Failed to create rag corpus: {str(e)}"
        }   

    return {
                "status": "success",
                "collection": collection,
                "message": f"Successfully created collection {COLLECTION_NAME}"
            }    


def close_connection(client):
    client.close()

#Check and return the rag corpus if it exists
def get_rag_corpus():
    corpora_pager = rag.list_corpora()
    for corpus in corpora_pager:
        if corpus.display_name == RAG_CORPUS_DISPLAY_NAME:
            rc = rag.get_corpus(corpus.name)
            return rc
    return None

def create_rag_corpus():
    
    embedding_model_config = rag.EmbeddingModelConfig(
        publisher_model="publishers/google/models/text-embedding-005"
    )
    #Step 1 : Connect vertex to Weaviate 
    try :
        print('Creating vector db...')
        vector_db = rag.Weaviate(
            weaviate_http_endpoint=WEAVIATE_HTTP_ENDPOINT,
            collection_name=COLLECTION_NAME,
            api_key=SM_WEAVIATE_API_KEY_RESOURCE,
        )
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": f"Failed to connect to Weaviate: {str(e)}"
        }

    print(f'Created vector_db : {vector_db}')

    #Step 2: create rag corpus
    try :
        print('Creating rag_corpus ...')
        rag_corpus = rag.create_corpus(
            display_name=RAG_CORPUS_DISPLAY_NAME,
            embedding_model_config=embedding_model_config,
            vector_db=vector_db,
        )

        print(f'Created rag_corpus {rag_corpus.name}')
        
        return {
            "status": "success",
            "rag_corpus_name": rag_corpus.name,
            "display_name": rag_corpus.display_name,
            "description": rag_corpus.description,
            "message": f"Successfully created RAG corpus '{rag_corpus.display_name}'"
        }

    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": f"Failed to create rag corpus: {str(e)}"
        }

def upload_file_to_corpus(rag_corpus_name):       
    print(f'Uploading file to rag corpus {rag_corpus_name}')
    rag_corpus = rag.get_corpus(rag_corpus_name)
    #rag_corpus = rag.get_corpus('projects/51718666097/locations/us-central1/ragCorpora/4611686018427387904')
    print(f'Retrieved corpus : {rag_corpus}')

    try: 
        print('Uploading file ...')
        path = os.path.join(DATA_DIR, DATA_FILE)
        rag_file = rag.upload_file(
            corpus_name=rag_corpus.name,
            path=path,
            display_name="Wiki collection",
            description="Wiki collection data",
        )

        print(f'Created rag_file: {rag_file}')
        rag.list_files(corpus_name=rag_corpus.name)
        return {
            "status": "success",
            "file_name": rag_file.name,
            "display_name": rag_file.display_name,
            "description": rag_file.description,
            "message": f"Successfully uploaded file '{rag_file.display_name}'"
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": f"Failed to upload file: {str(e)}"
        }



def create_rag_retrieval_tool(corpus_name):
    print(f'Creating rag retrieval tool for rag corpus {corpus_name}')

    rag_resource = rag.RagResource(
    rag_corpus=corpus_name,
    )
    print(f'Created rag_resource {rag_resource}')

    print('Creating rag_retrieval tool...')
    try :
        rag_retrieval_tool = Tool.from_retrieval(
            retrieval=rag.Retrieval(
                source=rag.VertexRagStore(
                    rag_resources=[rag_resource],  # Currently only 1 corpus is allowed.
                    similarity_top_k=10, # optional: number of top k documents to retrieve 
                    vector_distance_threshold=0.8, # optional: threshold for the retrieval
                ),
            )
        )
        print(f'Created rag_retrieval tool {rag_retrieval_tool}')

        return {
            "status": "success",
            "rag_retrieval_tool": rag_retrieval_tool,
            "message": f"Successfully created tool '{rag_retrieval_tool}'"
        }
        
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": f"Failed to create rag retrieval tool: {str(e)}"
        }
    
def create_rag_model_from_tool(tool):    

    try :
        print('Creating rag_model...')
        rag_model = GenerativeModel("gemini-2.0-flash", tools=[tool])
        print(f'Created rag_model: {rag_model}')

        return {
            "status": "success",
            "rag_model": rag_model,
            "message": f"Successfully created model '{rag_model}'"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": f"Failed to create model from tool: {str(e)}"
        }
    

def get_content_response(rag_model, content_prompt):

    print('generating content...')
    response = rag_model.generate_content(content_prompt)
    return response.text

def check_status(val, c):
    if val.get('status') == 'error':
        close_connection(c)
        sys.exit()

def get_status(status, msg):
     return {
            "status": status,
            "message": str(msg)
        }


def must_init():
    if PROJECT_ID == 'None':
        return get_status("error", "failed to get PROJECT_ID")
    elif WEAVIATE_HTTP_ENDPOINT == 'None':
        return get_status("error", "failed to get WEAVIATE_HTTP_ENDPOINT")  
    elif WEAVIATE_API_KEY == 'None':
        return get_status("error", "failed to get WEAVIATE_API_KEY") 
    elif SM_WEAVIATE_API_KEY_RESOURCE == 'None':
        return get_status("error", "failed to get SM_WEAVIATE_API_KEY_RESOURCE") 
    elif COLLECTION_NAME == 'None':
        return get_status("error", "failed to get COLLECTION_NAME") 
    elif RAG_CORPUS_DISPLAY_NAME == 'None':
        return get_status("error", "failed to get RAG_CORPUS_DISPLAY_NAME")     
    elif VERTEX_API_KEY == 'None':
        return get_status("error", "failed to get VERTEX_API_KEY") 
    
    if not os.path.exists(os.path.join(DATA_DIR, DATA_FILE)):
        return get_status("error", f"Missing data file {DATA_FILE} in directory {DATA_DIR}")

    return get_status("success", "All env vars present")                

vertexai.init(project=PROJECT_ID, location=LOCATION)

def main():
    st = must_init()
    if st.get('status') != 'success':
        print(f'Initialization error, err = {st.get("message")}')
        sys.exit(0)

    c= connect_and_get_client()
    rc = create_collection(c)
    if rc.get('status') != 'success':
        print(f'DB error, err = {st.get("message")}')
        sys.exit(0)
    

    #check if corpus is already created
    rc = get_rag_corpus()

    if rc == None:
        val = create_rag_corpus()
        check_status(val, c)

        corpus_name =   val['rag_corpus_name']  
        val = upload_file_to_corpus(corpus_name)
        check_status(val, c)
    else:
        corpus_name = rc.name

    val = create_rag_retrieval_tool(corpus_name)
    check_status(val, c)

    tool = val['rag_retrieval_tool']
    val = create_rag_model_from_tool(tool)
    check_status(val, c)

    model = val['rag_model']
    content_prompt = 'Summarize the history of computing in 3 points'
    resp = get_content_response(model, content_prompt)
    print(f'Response {resp}')
    close_connection(c)

if __name__== '__main__':
    main()
