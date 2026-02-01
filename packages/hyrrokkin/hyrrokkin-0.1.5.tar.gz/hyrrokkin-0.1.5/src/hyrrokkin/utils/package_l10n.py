#   Hyrrokkin - A visual modelling tool for constructing and executing directed graphs.
#
#   Copyright (C) 2022-2025 Visual Topology Ltd
#
#   Licensed under the MIT License

import os
import json

class PackageL10N:

    def __init__(self, languages, default_language, package_path):
        self.languages = languages
        self.default_language = default_language
        self.package_path = package_path

    def get_bundle(self, for_language=""):
        if not for_language or for_language not in self.languages:
            for_language = self.default_language
        if for_language in self.languages:
            filename = self.languages[for_language]["bundle_url"]
            filepath = os.path.join(self.package_path, filename)
            with open(filepath) as f:
                return (for_language, json.loads(f.read()))
        return ("", {})

    @staticmethod
    def load(package_content, package_path):
        if "l10n" in package_content:
            return PackageL10N(package_content["l10n"]["languages"], package_content["l10n"]["default_language"],package_path)
        else:
            return None