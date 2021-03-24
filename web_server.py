#!/usr/bin/env python3

# Modified from https://github.com/UoA-eResearch/dynamic_network_graph/blob/main/web_server.py
# See: https://uoa-eresearch.github.io/dynamic_network_graph/url_sync.html#URL_SYNC_TEST

import asyncio
import json
import logging
import websockets
import random
import signal
import sys

logging.basicConfig(level=logging.INFO)
logging.getLogger("asyncio").setLevel(logging.INFO)
logging.getLogger("websockets").setLevel(logging.INFO)

sessions = {}
try:
    with open("db.json", "r") as f:
        sessions = json.load(f)
        logging.info("loaded DB from file")
except Exception as e:
    logging.error(f"Error loading DB, starting fresh. {e}")
print(sessions)


def save():
    logging.info("Saving")
    safe_sess = {sid: {"data": sess["data"]}  # entries
                 for sid, sess in sessions.items()}
    with open("db.json", "w") as f:
        json.dump(safe_sess, f)


def receiveSignal(signalNumber, frame):
    logging.info("SIGTERM caught")
    sys.exit()


signal.signal(signal.SIGTERM, receiveSignal)


async def save_loop():
    while True:
        await asyncio.sleep(30)
        save()


async def app(websocket, path):
    try:
        async for message in websocket:
            data = json.loads(message)
            action = data.get("action")
            session_id = str(data.get("session_id"))
            logging.info(f"action:{action} session_id:{session_id}")
            sess = sessions.get(session_id)
            if session_id and not sess:
                sess = {
                    "data": "",
                    "users": set([websocket]),
                }
                sessions[session_id] = sess
            if sess and not sess.get("users"):
                sess["users"] = set([websocket])
            # if action == "create_session":
            #     session_id = str(random.randint(0, 9999))
            #     sessions[session_id] = {
            #         "data": "",
            #         "users": set([websocket]),
            #     }
            #     await websocket.send(json.dumps({"session_id": session_id}))
            if action == "connect":
                sess["users"].add(websocket)
                # Inform all connected users about the newly connected user
                message = json.dumps({"user_count": len(sess["users"])})
                await asyncio.wait([user.send(message) for user in sess["users"]])
            elif action == "request_data":
                await websocket.send(json.dumps({
                    "data": sess["data"]
                }))
            elif action == "send_data":
                sent_data = data.get("data")
                sess["data"] = data
                logging.info(
                    f"action:{action} session_id:{session_id}, data: {sent_data}")

                # Inform all connected users about the sent data
                message = json.dumps({"data": data})
                usercount = len(sess["users"])
                print(sess)
                logging.info(f"forwarding data to {usercount} users")
                await asyncio.wait([user.send(message) for user in sess["users"]])
            elif action == "highlight":
                sample_sites = data.get("sample_sites")
                sess["data"] = data
                logging.info(
                    f"action:{action} session_id:{session_id}, data: {sample_sites}")

                # Inform all connected users about the sent data
                message = json.dumps({"data": data})
                usercount = len(sess["users"])
                print(sess)
                logging.info(f"forwarding data to {usercount} users")
                await asyncio.wait([user.send(message) for user in sess["users"]])
            # elif action == "delete_entry":
            #     entry_id = data.get("entry_id")
            #     if sess["entries"].pop(entry_id, None):
            #         # Inform all connected users about the deleted entry
            #         message = json.dumps({"deleted_entry": entry_id})
            #         await asyncio.wait([user.send(message) for user in sess["users"]])
            else:
                logging.error(f"unsupported event: {data}")
    except websockets.exceptions.ConnectionClosedError as e:
        pass
        #logging.error(f"User disconnected: {e}")
    finally:
        for session_id, sess in sessions.items():
            if sess.get("users") and websocket in sess["users"]:
                sess["users"].remove(websocket)
                if len(sess["users"]) > 0:
                    # Inform all connected users about the disconnected user
                    message = json.dumps({"user_count": len(sess["users"])})
                    await asyncio.wait([user.send(message) for user in sess["users"]])

start_server = websockets.serve(app, "0.0.0.0", 6789)


def exception_handler(loop, context):
    logging.debug(context["message"])


asyncio.get_event_loop().set_exception_handler(exception_handler)

try:
    asyncio.get_event_loop().run_until_complete(asyncio.wait([
        start_server,
        save_loop()
    ]))
except BaseException as e:
    logging.error(f"{type(e)}. {e}")
    save()
