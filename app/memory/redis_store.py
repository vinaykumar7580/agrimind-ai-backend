import redis
import json

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

def save_chat(user_id, data):

    redis_client.rpush(
        f"chat:{user_id}",
        json.dumps(data)
    )

def get_chat(user_id):

    return redis_client.lrange(
        f"chat:{user_id}",
        0,
        -1
    )