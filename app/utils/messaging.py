import json
from spade.message import Message


class Messaging:

    @staticmethod
    def prepare_message(receiver, body, **kwargs):
        message = Message(to=receiver)
        
        for key, value in kwargs.items():
            message.set_metadata(key, value)

        message.body = body
        print(f"Sending message: {message}")
        return message

    