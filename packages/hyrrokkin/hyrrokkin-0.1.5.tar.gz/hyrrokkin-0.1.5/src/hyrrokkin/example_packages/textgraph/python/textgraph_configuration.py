#   Hyrrokkin - a library for building and running executable graphs
#
#   MIT License - Copyright (C) 2022-2025  Visual Topology Ltd

from hyrrokkin_engine.configuration_interface import ConfigurationInterface
import json

from .text_input_node import TextInputNode
from .word_frequency_node import WordFrequencyNode
from .table_display_node import TableDisplayNode
from .merge_frequencies_node import MergeFrequenciesNode
from .merge_text_node import MergeTextNode


class TextgraphConfiguration(ConfigurationInterface):

    # https://gist.github.com/sebleier/554280 with modifications
    DEFAULT_STOP_WORDS = ["i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours",
                          "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself",
                          "it", "its", "itself", "they", "them", "their", "theirs", "themselves", "what", "which",
                          "who", "whom", "this", "that", "these", "those", "am", "is", "are", "was", "were", "be",
                          "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an",
                          "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for",
                          "with", "about", "against", "between", "into", "through", "during", "before", "after",
                          "above", "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under",
                          "again", "further", "then", "once", "here", "there", "when", "where", "why", "how", "all",
                          "any", "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not",
                          "only", "own", "same", "so", "than", "too", "very", "can", "will", "just", "dont", "should",
                          "now"]

    def __init__(self, services):
        self.services = services
        self.clients = set()
        self.properties = None
        self.update_listeners = set()
        self.stop_words = []

    async def load(self):
        keys = await self.services.get_data_keys()
        if "stop_words" in keys:
            self.stop_words = json.loads((await self.services.get_data("stop_words")).decode())
        else:
            self.stop_words = TextgraphConfiguration.DEFAULT_STOP_WORDS


    def get_stop_words(self):
        return self.stop_words

    def add_update_listener(self, listener):
        self.update_listeners.add(listener)
        return listener

    def remove_update_listener(self, listener):
        self.update_listeners.remove(listener)

    async def notify_update_listeners(self):
        for update_listener in self.update_listeners:
            await update_listener()

    async def create_node(self, node_type_id, node_services):
        match node_type_id:
            case "text_input_node":
                return TextInputNode(node_services)
            case "word_frequency_node":
                return WordFrequencyNode(node_services)
            case "merge_frequencies_node":
                return MergeFrequenciesNode(node_services)
            case "merge_text_node":
                return MergeTextNode(node_services)
            case "table_display_node":
                return TableDisplayNode(node_services)
            case _:
                return None

    @staticmethod
    def encode(value, link_type):
        if value is not None:
            if link_type == "text":
                return value.encode("utf-8")
            elif link_type == "frequency_table":
                return json.dumps(value).encode("utf-8")
        return None

    @staticmethod
    def decode(encoded_bytes, link_type):
        if encoded_bytes is not None:
            if link_type == "text":
                return encoded_bytes.decode("utf-8")
            elif link_type == "frequency_table":
                return json.loads(encoded_bytes.decode("utf-8"))
        return None

    async def open_client(self, client):
        self.clients.add(client)

        async def handle_message(stop_words):
            self.stop_words = stop_words
            await self.services.set_data("stop_words", json.dumps(self.stop_words).encode())
            for other_client in self.clients:
                if other_client != client:
                    other_client.send_message(stop_words)
            await self.notify_update_listeners()

        client.set_message_handler(handle_message)
        client.send_message(self.stop_words)

    async def close_client(self, client):
        self.clients.remove(client)
