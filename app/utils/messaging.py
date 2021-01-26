import json
from spade.message import Message


class Messaging:

    @staticmethod
    def prepare_message(sender, receiver, body, **kwargs):
        message = Message(to=receiver, sender= sender)
        
        for key, value in kwargs.items():
            message.set_metadata(key, value)

        message.body = body
        print(f"Message from {message.sender.localpart} to {message.to.localpart} : {message.metadata['performative']}")
        return message

    