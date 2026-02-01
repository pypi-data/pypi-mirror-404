# VectorDBCostSavingInspector

This is a tool designed to inspect vertor database usage and find opportunities to reduce cost. The current version support Pinecone usage inspection based on vector's last access timestamp. 

If your vector database is not Pinecone, we will estimate saving based on your vector database use cases. 

If your Pinecone database does not have meta data about last access timestamp, we will estimate saving based on your vector database use cases. But we strongly suggest you add one. 

## Setup
1. Install python package

```
python3 -m pip install vector-db-cost-inspector
```
2. Environment Variables 

Set the following environment variables (or create a .env file):

```
export PINECONE_API_KEY="your-pinecone-key"
export PINECONE_INDEX_NAME="your-index-name"
```

**Note:** This inspection tool only run in your machine. The Pinecone API key is only read by the inspection tool and won't be uploaded to cloud. We guarantee we don't have access to your Pinecone API key. This is a open source python tool. You can check our code if you want anytime.  

### Prerequisites

- A Pinecone Index.
- Vectors in Pinecone MUST have a metadata field named created_at (Unix timestamp) for the time-based logic to work.

## Usage

### Run the inspection

```
vector-db-cost-inspector
```
