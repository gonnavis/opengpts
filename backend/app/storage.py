import os
from datetime import datetime

import orjson
from langchain.schema.messages import messages_from_dict
from langchain.utilities.redis import get_client


def assistants_list_key(user_id: str):
    return f"opengpts:{user_id}:assistants"


def assistant_key(user_id: str, assistant_id: str):
    return f"opengpts:{user_id}:assistant:{assistant_id}"


def threads_list_key(user_id: str):
    return f"opengpts:{user_id}:threads"


def thread_key(user_id: str, thread_id: str):
    return f"opengpts:{user_id}:thread:{thread_id}"


def thread_messages_key(user_id: str, thread_id: str):
    # Needs to match key used by RedisChatMessageHistory
    # TODO we probably want to align this with the others
    return f"message_store:{user_id}:{thread_id}"


assistant_hash_keys = ["assistant_id", "name", "config", "updated_at"]
thread_hash_keys = ["assistant_id", "thread_id", "name", "updated_at"]


def dump(map: dict) -> dict:
    return {k: orjson.dumps(v) if v is not None else None for k, v in map.items()}


def load(keys: list[str], values: list[bytes]) -> dict:
    return {k: orjson.loads(v) if v is not None else None for k, v in zip(keys, values)}


def list_assistants(user_id: str):
    client = get_client(os.environ.get("REDIS_URL"))
    ids = [orjson.loads(id) for id in client.smembers(assistants_list_key(user_id))]
    with client.pipeline() as pipe:
        for id in ids:
            pipe.hmget(assistant_key(user_id, id), *assistant_hash_keys)
        assistants = pipe.execute()
    return [load(assistant_hash_keys, values) for values in assistants]


def put_assistant(user_id: str, assistant_id: str, *, name: str, config: dict):
    saved = {
        "user_id": user_id,
        "assistant_id": assistant_id,
        "name": name,
        "config": config,
        "updated_at": datetime.utcnow(),
    }
    client = get_client(os.environ.get("REDIS_URL"))
    with client.pipeline() as pipe:
        pipe.sadd(assistants_list_key(user_id), orjson.dumps(assistant_id))
        pipe.hset(assistant_key(user_id, assistant_id), mapping=dump(saved))
        pipe.execute()
    return saved


def list_threads(user_id: str):
    client = get_client(os.environ.get("REDIS_URL"))
    ids = [orjson.loads(id) for id in client.smembers(threads_list_key(user_id))]
    with client.pipeline() as pipe:
        for id in ids:
            pipe.hmget(thread_key(user_id, id), *thread_hash_keys)
        threads = pipe.execute()
    return [load(thread_hash_keys, values) for values in threads]


def get_thread_messages(user_id: str, thread_id: str):
    client = get_client(os.environ.get("REDIS_URL"))
    messages = client.lrange(thread_messages_key(user_id, thread_id), 0, -1)
    return {
        "messages": [
            m.dict()
            for m in messages_from_dict([orjson.loads(m) for m in messages[::-1]])
        ],
    }


def put_thread(user_id: str, thread_id: str, *, assistant_id: str, name: str):
    saved = {
        "user_id": user_id,
        "thread_id": thread_id,
        "assistant_id": assistant_id,
        "name": name,
        "updated_at": datetime.utcnow(),
    }
    client = get_client(os.environ.get("REDIS_URL"))
    with client.pipeline() as pipe:
        pipe.sadd(threads_list_key(user_id), orjson.dumps(thread_id))
        pipe.hset(thread_key(user_id, thread_id), mapping=dump(saved))
        pipe.execute()
    return saved


if __name__ == "__main__":
    print(list_assistants("133"))
    print(list_threads("123"))
    put_assistant("123", "i-am-a-test", name="Test Agent", config={"tags": ["hello"]})
    put_thread("123", "i-am-a-test", "test1", name="Test Thread")
