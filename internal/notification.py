from typing import Literal


# Pubsubがないのでコメントアウト

# pubsub_client = pubsub_v1.PublisherClient()

# topic = {"email": pubsub_client.topic_path(os.environ.get("GOOGLE_CLOUD_PROJECT"), "email"),
#          "push": pubsub_client.topic_path(os.environ.get("GOOGLE_CLOUD_PROJECT"), "push")}


def publish(type: Literal["email", "push"], data: dict):
    print(type, data)
    # data = json.dumps(data).encode("utf-8")
    # future = pubsub_client.publish(push_topic_path, data=data)
    # future.result()
