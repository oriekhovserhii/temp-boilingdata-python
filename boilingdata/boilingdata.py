import uuid
import asyncio
import logging
import json
from typing import Callable, Dict, Union, Any
from websockets import connect as ws_connect

from common.credentials import swap_bd_creds_for_aws_creds
from common.signature import get_signed_wss_url


class BoilingData:
    def __init__(self, username: str, password: str, region: str, log_level: str = "info", global_callbacks: Dict[str, Callable] = None):
        self.query_finished_events = {}
        self.username = username
        self.password = password
        self.region = region
        self.socket_instance = {
            "queries": {},
            "query_callbacks": {},
            "last_activity": None,
            "socket": None,
        }
        self.props = {
            "logLevel": log_level,
            "globalCallbacks": global_callbacks or {},
        }
        self.logger = logging.getLogger("boilingdata")
        self.logger.setLevel(logging.INFO)

    async def connect(self) -> None:
        async def handle_socket_messages() -> None:
            async for msg in self.socket_instance["socket"]:
                self.logger.info("Received message: %s", msg)
                data = json.loads(msg)

                await self.handle_socket_message(data)

        aws_credentials = await swap_bd_creds_for_aws_creds(self.username, self.password)
        signed_websocket_url = await get_signed_wss_url(aws_credentials, self.region, "wss", "/")

        self.socket_instance["socket"] = await ws_connect(signed_websocket_url)

        if "onSocketOpen" in self.props["globalCallbacks"]:
            self.props["globalCallbacks"]["onSocketOpen"]()

        asyncio.create_task(handle_socket_messages())

    async def close(self) -> None:
        if self.socket_instance["socket"]:
            await self.socket_instance["socket"].close()

        if "onSocketClose" in self.props["globalCallbacks"]:
            self.props["globalCallbacks"]["onSocketClose"]()

    async def handle_socket_message(self, message: Dict[str, Any]) -> None:
        event_type = message.get("messageType", "")
        request_id = message.get("requestId", "")
        is_query_finished = self.process_batch_info(message)
        callback_name = self.map_event_type_to_callback_name(event_type, message)
        
        global_callback = self.socket_instance["query_callbacks"].get(request_id, {}).get(callback_name, None)
        query_callback = self.props["globalCallbacks"].get(callback_name, None)

        if global_callback:
            global_callback(message)
        if query_callback:
            query_callback(message)
        if is_query_finished:
            all_data = self.socket_instance["queries"][request_id]["data"]
            global_callback = self.socket_instance["query_callbacks"].get(request_id, {}).get("onQueryFinished", None)
            if global_callback:
                global_callback(all_data)
            query_callback = self.props["globalCallbacks"].get("onQueryFinished", None)
            if query_callback:
                query_callback(all_data)
            query_finished_event = self.query_finished_events.get(request_id)
            if query_finished_event: 
                query_finished_event.set()



    def map_event_type_to_callback_name(self, event_type: str, message: Dict[str, Any]) -> str:
        if event_type == "LOG_MESSAGE":
            log_level = message.get("logLevel", "").upper()
            if log_level == "INFO":
                return "onLogInfo"
            elif log_level == "ERROR":
                return "onLogError"
            elif log_level == "WARN":
                return "onLogWarn"
            elif log_level == "DEBUG":
                return "onLogDebug"
        else:
            callback_mapping = {
                "REQUEST": "onRequest",
                "DATA": "onData",
                "INFO": "onInfo",
                "LAMBDA_EVENT": "onLambdaEvent",
                "QUERY_FINISHED": "onQueryFinished",
            }
            return callback_mapping.get(event_type, "")

    async def query(self, sql: str,  keys: list = None) -> Any:
        query_finished_event = await self.exec_query(sql, engine, keys)
        await query_finished_event.wait()

        request_id = query_finished_event.request_id
        all_data = self.socket_instance["queries"][request_id]["data"]
        del self.socket_instance["queries"][request_id]
        del self.query_finished_events[request_id]

        return all_data

    async def exec_query(self, sql: str, keys: list = None, callbacks: dict = None) -> None:
        self.logger.info("runQuery: %s", sql)
        request_id = str(uuid.uuid4())

        payload = {
            "messageType": "SQL_QUERY",
            "sql": sql,
            "keys": keys or [],
            "engine": "DUCKDB",
            "requestId": request_id,
        }


        self.socket_instance["query_callbacks"][request_id] = callbacks or {}

        query_finished_event = asyncio.Event()
        query_finished_event.request_id = request_id
        self.query_finished_events[request_id] = query_finished_event
        await self.socket_instance["socket"].send(json.dumps(payload))

        return query_finished_event

    def is_data_response(self, message):
        return message.get('messageType') == 'DATA'

    def process_batch_info(self, message):
        if not self.is_data_response(message):
            return False

        if not message.get('requestId') or not message.get('batchSerial') or not message.get('totalBatches') or message['batchSerial'] <= 0:
            return False
        
        query_id = message['requestId']
        if query_id not in self.socket_instance["queries"]:
            self.socket_instance["queries"][query_id] = {
                'receivedBatches': set(),
                'receivedSplitBatches': {},
                'receivedSubBatches': {},
                'data': [],
            }
        
        query_info = self.socket_instance["queries"][query_id]
        query_info['receivedBatches'].add(message['batchSerial'])
        # Store the data from the current message
        query_info['data'].extend(message['data'])

        if message.get('splitSerial') and message.get('totalSplitSerials'):
            if message['batchSerial'] not in query_info['receivedSplitBatches']:
                query_info['receivedSplitBatches'][message['batchSerial']] = set()
            
            received_split_serials = query_info['receivedSplitBatches'][message['batchSerial']]
            received_split_serials.add(message['splitSerial'])

            if len(received_split_serials) < message['totalSplitSerials']:
                return False

        parent_batch_serial = message['splitSerial'] if message.get('totalSplitSerials') else message['batchSerial']

        if message.get('subBatchSerial') and message.get('totalSubBatches'):
            if parent_batch_serial not in query_info['receivedSubBatches']:
                query_info['receivedSubBatches'][parent_batch_serial] = set()
            
            received_sub_batches = query_info['receivedSubBatches'][parent_batch_serial]
            received_sub_batches.add(message['subBatchSerial'])

            if len(received_sub_batches) < message['totalSubBatches']:
                return False

        if len(query_info['receivedBatches']) < message['totalBatches']:
            return False
        
        return True

    