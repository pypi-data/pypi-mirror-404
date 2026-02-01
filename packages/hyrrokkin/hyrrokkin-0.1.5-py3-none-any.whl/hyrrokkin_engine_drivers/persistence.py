from hyrrokkin_engine.persistence_interface import PersistenceInterface

class Persistence(PersistenceInterface):

    def __init__(self):
        self.target_id = None
        self.target_type = None
        self.property_update_listeners = []
        self.data_update_listeners = []
        self.callbacks_enabled = True

    def configure(self, target_id, target_type):
        self.target_id = target_id
        self.target_type = target_type

    @staticmethod
    def check_valid_data_key(key):
        for c in key:
            if not c.isalnum() and c != '_':
                raise ValueError("data key can only contain alphanumeric characters and underscores")

    @staticmethod
    def check_valid_data_value(data):
        if data is None:
            return True
        return isinstance(data, bytes)

    def add_properties_update_listener(self, listener):
        self.property_update_listeners.append(listener)
        return listener

    def add_data_update_listener(self, listener):
        self.data_update_listeners.append(listener)
        return listener

    def properties_updated(self, properties):
        if self.callbacks_enabled:
            for listener in self.property_update_listeners:
                listener(self.target_id, self.target_type, properties)

    def data_updated(self, key, value):
        if self.callbacks_enabled:
            for listener in self.data_update_listeners:
                listener(self.target_id, self.target_type, key, value)

    def enable_callbacks(self):
        self.callbacks_enabled = True

    def disable_callbacks(self):
        self.callbacks_enabled = False
