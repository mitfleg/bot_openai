import json
import requests
import random
from handlers.common import getConfig


targetID = ""
targetHash = ""

variable = getConfig("discord")


def PassPromptToSelfBot(prompt: str):
 
    payload = {"type": 2,
               "application_id": "",
               "guild_id": variable['SERVER_ID'],
               "channel_id": variable['CHANNEL_ID'],
               "session_id": "",
               "data": {"version": "",
                        "id": "",
                        "name": "imagine",
                        "type": 1,
                        "options": [{"type": 3, "name": "prompt", "value": prompt}],
                        "application_command": {"id": "",
                                                "application_id": "",
                                                "version": "",
                                                "default_permission": True,
                                                "default_member_permissions": None,
                                                "type": 1,
                                                "name": "imagine",
                                                "description": "There are endless possibilities...",
                                                "dm_permission": True,
                                                "options": [{"type": 3, "name": "prompt", "description": "The prompt to imagine", "required": True}]},
                        "attachments": []}}

    header = {
        'authorization': variable['SALAI_TOKEN']
    }

    header = {"authorization": variable["SALAI_TOKEN"]}

    response = requests.post(
        "https://discord.com/api/v9/interactions", json=payload, headers=header
    )
    return response


def Upscale(index: int, messageId: str, messageHash: str):
    payload = {
        "type": 3,
        "nonce": "1" + "".join([str(random.randint(0, 9)) for i in range(18)]),
        "guild_id": variable["SERVER_ID"],
        "channel_id": variable["CHANNEL_ID"],
        "message_flags": 0,
        "message_id": messageId,
        "application_id": "",
        "session_id": "",
        "data": {
            "component_type": 2,
            "custom_id": "MJ::JOB::upsample::{}::{}".format(index, messageHash),
        },
    }
    header = {"authorization": variable["SALAI_TOKEN"]}
    response = requests.post(
        "https://discord.com/api/v9/interactions", json=payload, headers=header
    )
    return response


def MaxUpscale(messageId: str, messageHash: str):
    payload = {
        "type": 3,
        "nonce": "1" + "".join([str(random.randint(0, 9)) for i in range(18)]),
        "none": "",
        "guild_id": variable["SERVER_ID"],
        "channel_id": variable["CHANNEL_ID"],
        "message_flags": 0,
        "message_id": str(messageId),
        "application_id": "",
        "session_id": "",
        "data": {
            "component_type": 2,
            "custom_id": "MJ::JOB::upsample_max::1::{}::SOLO".format(messageHash),
        },
    }

    header = {"authorization": variable["SALAI_TOKEN"]}
    response = requests.post(
        "https://discord.com/api/v9/interactions", json=payload, headers=header
    )
    return response


def Variation(index: int, messageId: str, messageHash: str):
    payload = {
        "type": 3,
        "guild_id": variable["SERVER_ID"],
        "channel_id": variable["CHANNEL_ID"],
        "message_flags": 0,
        "message_id": messageId,
        "application_id": "",
        "session_id": "",
        "data": {
            "component_type": 2,
            "custom_id": "MJ::JOB::variation::{}::{}".format(index, messageHash),
        },
    }
    header = {"authorization": variable["SALAI_TOKEN"]}
    response = requests.post(
        "https://discord.com/api/v9/interactions", json=payload, headers=header
    )
    return response
