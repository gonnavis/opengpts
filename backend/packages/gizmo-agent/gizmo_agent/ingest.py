import os

from agent_executor.upload import IngestRunnable
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema.runnable import ConfigurableField
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores.redis import Redis

index_schema = {
    "tag": [{"name": "namespace"}],
}
vstore = Redis(
    redis_url=os.environ["REDIS_URL"],
    index_name="opengpts",
    embedding=OpenAIEmbeddings(),
    index_schema=index_schema,
)


ingest_runnable = IngestRunnable(
    text_splitter=RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200),
    vectorstore=vstore,
    input_key="file_contents",
).configurable_fields(
    user_id=ConfigurableField(
        id="user_id",
        annotation=str,
        name="User ID",
    ),
    assistant_id=ConfigurableField(
        id="assistant_id",
        annotation=str,
        name="Assistant ID",
    ),
)
