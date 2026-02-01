
class Registry:

    def __init__(self):
        self.configuration_factories = {}

    def register_configuration_factory(self, package_id, configuration_factory):
        self.configuration_factories[package_id] = configuration_factory

    def defines_configuration(self, package_id):
        return package_id in self.configuration_factories

    def create_configuration(self, package_id, configuration_services):
        return self.configuration_factories[package_id](configuration_services)

registry = Registry()