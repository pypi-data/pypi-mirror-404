#   Hyrrokkin - a library for building and running executable graphs
#
#   MIT License - Copyright (C) 2022-2025  Visual Topology Ltd
#
#   Permission is hereby granted, free of charge, to any person obtaining a copy of this software
#   and associated documentation files (the "Software"), to deal in the Software without
#   restriction, including without limitation the rights to use, copy, modify, merge, publish,
#   distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the
#   Software is furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in all copies or
#   substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
#   BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#   NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#   DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import argparse
import sys
import os
import signal
import logging
import asyncio
import time
import importlib
import json

from hyrrokkin_engine.registry import registry
from hyrrokkin_engine.message_utils import MessageUtils
from hyrrokkin_engine.graph_executor import GraphExecutor
from hyrrokkin_engine_drivers.persistence_memory import PersistenceMemory
from hyrrokkin_engine_drivers.persistence_filesystem import PersistenceFileSystem

class ExecutionWorker:

    MAX_RETRIES = 4
    RETRY_DELAY_MS = 1000

    def __init__(self, host_name, port, verbose):

        self.host_name = host_name
        self.port = port
        self.verbose = verbose
        self.pid = os.getpid()

        self.reader = None
        self.writer = None
        self.graph_executor = None
        self.injected_inputs = {}
        self.output_listeners = {}
        self.persistence = {}
        self.persistence_mode = "" # filesystem | memory
        self.execution_folder = None
        self.running = False
        self.read_only = False
        self.listening_port = None
        self.running_task = None
        self.running_task_name = None
        self.logger = logging.getLogger("execution_worker")

    async def run(self):
        retry = 0
        while True:
            try:
                self.reader, self.writer = await asyncio.open_connection(self.host_name, self.port)
                break
            except Exception as ex:
                retry += 1
                if retry > self.MAX_RETRIES:
                    raise ex
                time.sleep(self.RETRY_DELAY_MS/1000)

        msg = await self.receive_message()
        control_packet = msg[0]
        action = control_packet["action"]

        if self.verbose:
            self.logger.info("init: "+ json.dumps(control_packet))

        if action == "init":
            await self.init(control_packet)
        else:
            raise Exception("Protocol error")

        self.running = True
        while self.running:
            try:
                msg = await self.receive_message()
                if msg is None:
                    break
                try:
                    await self.handle_message(*msg)
                except:
                    self.logger.exception("handle_message")
            except:
                self.running = False
        self.graph_executor.close()
        self.writer.close()
        await self.writer.wait_closed()

    async def send_message(self, *message_parts):
        self.send_message_sync(*message_parts)
        await self.writer.drain()

    def send_message_sync(self, *message_parts):
        if self.verbose:
            self.logger.info("send_message: "+ json.dumps(message_parts[0]))
        message_bytes = MessageUtils.encode_message(*message_parts)
        self.writer.write(len(message_bytes).to_bytes(4, "big"))
        self.writer.write(message_bytes)

    async def receive_message(self):
        message_length_bytes = await self.reader.read(4)
        if message_length_bytes == 0:
            return None
        message_length = int.from_bytes(message_length_bytes, "big")
        message_bytes = await self.reader.readexactly(message_length)
        message_parts = MessageUtils.decode_message(message_bytes)
        return message_parts

    def get_persistence(self, target_id, target_type):
        key = target_id+":"+target_type
        if key in self.persistence:
            return self.persistence[key]
        if self.persistence_mode == "filesystem":
            persistence = PersistenceFileSystem(root_folder=self.execution_folder, read_only=self.read_only)
        else:
            persistence = PersistenceMemory()
        persistence.configure(target_id, target_type)
        self.persistence[key] = persistence
        return persistence

    def track_persistence_changes(self, target_id, target_type):
        if self.read_only:
            return
        key = target_id + ":" + target_type
        persistence = self.persistence[key]
        persistence.add_properties_update_listener(
            lambda target_id, target_type, properties: self.properties_updated(target_id, target_type, properties))
        persistence.add_data_update_listener(
            lambda target_id, target_type, key, value: self.data_updated(target_id, target_type, key, value))

    def remove_persistence(self, target_id, target_type):
        key = target_id + ":" + target_type
        if key in self.persistence:
            del self.persistence[key]

    def properties_updated(self, target_id, target_type, properties):
        self.send_message_sync({
            "action": "set_properties",
            "target_id": target_id,
            "target_type": target_type,
            "properties": properties
        })

    def data_updated(self, target_id, target_type, key, value):
        self.send_message_sync({
            "action": "set_data",
            "target_id": target_id,
            "target_type": target_type,
            "key": key
        }, value)

    async def set_properties(self, o):
        target_id = o["target_id"]
        target_type = o["target_type"]
        properties = o["properties"]
        persistence = self.get_persistence(target_id,target_type)
        persistence.disable_callbacks()
        await persistence.set_properties(properties)
        persistence.enable_callbacks()

    async def set_data(self, o, data_value):
        target_id = o["target_id"]
        target_type = o["target_type"]
        key = o["key"]
        persistence = self.get_persistence(target_id,target_type)
        persistence.disable_callbacks()
        await persistence.set_data(key,data_value)
        persistence.enable_callbacks()

    async def add_node(self,o):
        node_id = o["node_id"]
        node_type_id = o["node_type_id"]
        copy_from_node_id = o.get("copy_from_node_id","")
        package_id = node_type_id.split(":")[0]
        node_type_id = node_type_id.split(":")[1]
        persistence = self.get_persistence(node_id,"node")
        self.track_persistence_changes(node_id, "node")
        await self.graph_executor.add_node(node_id, package_id, node_type_id, persistence, copy_from_node_id)

    async def add_link(self,o):
        await self.graph_executor.add_link(o["link_id"], o["from_node_id"],
                                           o["from_port"],
                                           o["to_node_id"], o["to_port"])

    async def add_package(self,o):
        package_id = o["package_id"]
        package_version = o["schema"].get("metadata",{}).get("version","")
        package_folder = o["folder"]
        persistence = self.get_persistence(package_id,"configuration")
        self.track_persistence_changes(package_id, "configuration")
        services = await self.graph_executor.create_configuration_service(package_id, package_version, package_folder, persistence)
        instance = registry.create_configuration(package_id, services)
        await self.graph_executor.add_package(o["package_id"], o["schema"], package_folder,instance)

    async def inject_input(self, o, *encoded_bytes):
        decoded_values = []
        for b in encoded_bytes:
            decoded_values.append(self.graph_executor.decode_value(o["node_id"], o["input_port_name"], b))
        await self.graph_executor.inject_input(o["node_id"], o["input_port_name"], decoded_values)

    async def remove_injected_input(self, o):
        await self.graph_executor.remove_injected_input(o["node_id"], o["input_port_name"])

    def add_output_listener(self, o):
        self.graph_executor.add_output_listener(o["node_id"], o["output_port_name"])

    def remove_output_listener(self, o):
        self.graph_executor.remove_output_listener(o["node_id"], o["output_port_name"])

    async def pause(self):
        await self.graph_executor.pause()
        self.send_message_sync({"action": "note_paused"})

    async def resume(self,o):
        await self.graph_executor.resume()
        self.send_message_sync({"action": "note_resumed"})

    def close(self):
        self.running = False
        self.graph_executor.close()
        
    async def handle_message(self, control_packet, *extras):
        if self.verbose:
            self.logger.info("handle_message: "+ json.dumps(control_packet))
        action = control_packet.get("action","?")
        match action:
            case "add_package":
                await self.add_package(control_packet)
            case "packages_added":
                self.send_message_sync({"action":"init_complete", "listening_port":self.listening_port})
            case "add_node":
                await self.add_node(control_packet)
            case "set_properties":
                await self.set_properties(control_packet)
            case "set_data":
                await self.set_data(control_packet, *extras)
            case "add_link":
                await self.add_link(control_packet)
            case "inject_input":
                await self.inject_input(control_packet, *extras)
            case "remove_injected_input":
                await self.remove_injected_input(control_packet)
            case "add_output_listener":
                self.add_output_listener(control_packet)
            case "remove_output_listener":
                self.remove_output_listener(control_packet)
            case "pause":
                await self.pause()
            case "resume":
                await self.resume(control_packet)
            case "close":
                self.close()
            case "open_session":
                session_id = control_packet["session_id"]
                self.graph_executor.open_session(session_id)
            case "close_session":
                session_id = control_packet["session_id"]
                self.graph_executor.close_session(session_id)
            case "open_client":
                session_id = control_packet["session_id"]
                client_id = control_packet["client_id"]
                await self.graph_executor.open_client(control_packet["target_id"],
                                    control_packet["target_type"],
                                    session_id,
                                    client_id,
                                    control_packet["client_options"])
            case "client_message":
                session_id = control_packet["session_id"]
                client_id = control_packet["client_id"]
                await self.graph_executor.recv_message(control_packet["target_id"],
                                    control_packet["target_type"],
                                    session_id,
                                    client_id,
                                    *extras)
            case "close_client":
                session_id = control_packet["session_id"]
                client_id = control_packet["client_id"]
                await self.graph_executor.close_client(control_packet["target_id"],
                                        control_packet["target_type"],
                                        session_id,
                                        client_id)
            case "stop_node":
                await self.graph_executor.stop_node(control_packet["node_id"])
                self.send_message_sync({"action":"node_stopped", "node_id": control_packet["node_id"]})
            case "restart_node":
                await self.graph_executor.restart_node(control_packet["node_id"])
            case "remove_node":
                await self.graph_executor.remove_node(control_packet["node_id"])
                self.remove_persistence(control_packet["node_id"],"node")
            case "remove_link":
                await self.graph_executor.remove_link(control_packet["link_id"])
            case "clear":
                await self.graph_executor.clear()
            case "run_task":
                await self.run_task(control_packet, *extras)
            case _:
                self.logger.warning(f"Unhandled action: {action}")

    async def run_task(self, control_packet, *extras):
        input_ports = control_packet["input_ports"]
        output_port_names = control_packet["output_ports"]
        task_name = control_packet["task_name"]
        self.logger.info(f"Running task: {task_name}")
        await self.graph_executor.pause()
        for (name,descr) in input_ports.items():
            node_id, input_port_name = name.split(":")
            values = []
            for idx in range(descr["start_index"],descr["end_index"]):
                values.append(self.graph_executor.decode_value(node_id, input_port_name, extras[idx]))
            await self.graph_executor.inject_input(node_id, input_port_name, values)
        self.running_task = { "outputs": output_port_names }
        self.running_task_name = task_name
        await self.graph_executor.resume()

    async def forward_output_value(self, node_id, output_port, value):
        encoded_value_bytes = self.graph_executor.encode_value(node_id, output_port, value)
        self.send_message_sync({"action":"output_notification", "node_id": node_id, "output_port_name":output_port},
                               encoded_value_bytes)

    def execution_monitor(self, is_complete):
        if is_complete:
            self.send_message_sync({"action":"execution_complete", "count_failed": self.graph_executor.count_failed(),
                                    "failures": self.graph_executor.get_failures() })
            if self.running_task is not None:
                output_port_ids = self.running_task["outputs"]
                output_port_values = []

                for output_port_id in output_port_ids:
                    node_id, output_port_name = output_port_id.split(":")
                    value = self.graph_executor.get_output_value(node_id, output_port_name)
                    encoded_value = self.graph_executor.encode_value(node_id, output_port_name, value)
                    output_port_values.append(encoded_value)
                self.send_message_sync({"action": "task_complete",
                                        "task_name": self.running_task_name,
                                        "output_ports": output_port_ids,
                                        "failures": self.graph_executor.get_failures()},
                                       *output_port_values)
                self.running_task = None
                self.running_task_name = None

        else:
            self.send_message_sync({"action": "execution_started"})

    def set_status(self, origin_id, origin_type, state, message):
        self.send_message_sync({"action":"update_status", "origin_id":origin_id, "origin_type":origin_type, "status":state, "message":message})

    def set_node_execution_state(self, at_time, node_id, execution_state, exn=None, is_manual=False):
        self.send_message_sync({"action": "update_execution_state",
                                "at_time": at_time,
                                "node_id": node_id,
                                "execution_state": execution_state,
                                "is_manual": is_manual,
                                "exn": None if exn is None else str(exn)})

    def send_client_message(self, origin_id, origin_type, session_id, client_id, *msg):
        self.send_message_sync({"action": "client_message", "origin_id":origin_id, "origin_type":origin_type, "session_id":session_id, "client_id":client_id},*msg)

    def send_request_open_client_callback(self, origin_id, origin_type, session_id, client_name):
        self.send_message_sync(
            {"action": "request_open_client", "origin_id": origin_id, "origin_type": origin_type,
             "session_id":session_id, "client_name": client_name})

    def create_configuration_factory(self, configuration_class):
        return lambda configuration_services: configuration_class(configuration_services)

    async def init(self, control_packet):
        self.read_only = control_packet["read_only"]
        paused = control_packet["paused"]

        self.persistence_mode = control_packet.get("persistence_mode","memory")
        self.execution_folder = control_packet.get("execution_folder",None)
        worker_configuration = control_packet["worker_configuration"]
        for package_id in worker_configuration["packages"]:
            configuration_path = worker_configuration["packages"][package_id]["configuration_class"]
            configuration_module = importlib.import_module(".".join(configuration_path.split(".")[:-1]))
            configuration_class = getattr(configuration_module, configuration_path.split(".")[-1])
            registry.register_configuration_factory(package_id, self.create_configuration_factory(configuration_class))

        async def output_notification_callback(node_id, output_port, value):
            await self.forward_output_value(node_id, output_port, value)

        self.graph_executor = GraphExecutor(
                                    execution_monitor_callback=lambda is_complete: self.execution_monitor(is_complete),
                                    status_callback=lambda *args: self.set_status(*args),
                                    node_execution_callback=lambda *args: self.set_node_execution_state(*args),
                                    message_callback=lambda *args: self.send_client_message(*args),
                                    output_notification_callback=output_notification_callback,
                                    request_open_client_callback=lambda *args: self.send_request_open_client_callback(*args),
                                    paused=paused)

        # self.server = Server(self.graph_executor, self.host_name, self.verbose)
        # self.listening_port = await self.server.start()
        # print(self.listening_port)



def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("host",type=str,help="host name")
    parser.add_argument("port",type=int,help="port number")
    parser.add_argument("--verbose", action="store_true", help="Print verbose output to console")

    args = parser.parse_args()
    os.putenv('PYTHONPATH',os.getcwd())

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    worker = ExecutionWorker(args.host,args.port,args.verbose)

    def handler(signum, frame):
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(0)

    signal.signal(3, handler)

    asyncio.run(worker.run())

if __name__ == '__main__':
    main()




