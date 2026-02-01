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



class ExpressionChecker:

    def __init__(self):
        self.unary_operator_typemaps = {}
        self.binary_operator_typemaps = {}
        self.function_typemaps = {}
        self.literal_typemapper = None

    def add_unary_operator_types(self, name,output_type,input_type):
        if name not in self.unary_operator_typemaps:
            self.unary_operator_typemaps[name] = []
        self.unary_operator_typemaps[name].append([output_type,input_type])

    def add_binary_operator_types(self, name,output_type, input_type1, input_type2):
        if name not in self.binary_operator_typemaps:
            self.binary_operator_typemaps[name] = []
        self.binary_operator_typemaps[name].append([output_type,input_type1,input_type2])

    def add_function_types(self, name,output_type,*input_types):
        if name not in self.function_typemaps:
            self.function_typemaps[name] = []
        self.function_typemaps[name].append([output_type]+input_types)

    def add_literal_typemapper(self, mapper_fn):
        self.literal_typemapper = mapper_fn

    def typematch(self, candidate_types, typemap_types):
        if len(candidate_types) != len(typemap_types):
            return False
        for idx in range(0,len(candidate_types)):
            if candidate_types[idx] != typemap_types[idx]:
                if typemap_types[idx] != "*":
                    return False
        return True

    def check_expression(self, parsed_expression, name_typemap):
        if "name" in parsed_expression:
            if parsed_expression["name"] not in name_typemap:
                return {"error_type":"invalid_name", "name":parsed_expression["name"], "context": parsed_expression}
            else:
                parsed_expression["type"] = name_typemap[parsed_expression["name"]]
                return None

        if "literal" in parsed_expression:
            typename = self.literal_typemapper(parsed_expression["literal"])
            if typename is None:
                return {"error_type":"literal_type_error", "literal":parsed_expression["literal"], "context": parsed_expression}
            else:
                parsed_expression["type"] = typename
                return None

        if ("operator" in parsed_expression or "function" in parsed_expression):
            for idx in range(0,len(parsed_expression["args"])):
                error = self.check_expression(parsed_expression["args"][idx], name_typemap)
                if error is not None:
                    return error

            types = []
            for arg in parsed_expression["args"]:
                types.append(arg["type"])

            if ("operator" in parsed_expression):
                if len(parsed_expression["args"]) == 1:
                    typemap = self.unary_operator_typemaps.get(parsed_expression["operator"],None)
                else:
                    typemap = self.binary_operator_typemaps.get(parsed_expression["operator"],None)

            else:
                typemap = self.function_typemaps.get(parsed_expression["function"],None)

            if typemap is None:
                # operator or function name lookup failed
                if "operator" in parsed_expression:
                    return {
                        "error_type": "operator_type_missing",
                        "operator": parsed_expression["operator"],
                        "context": parsed_expression
                    }
                else:
                    return {
                        "error_type": "function_type_missing",
                        "function": parsed_expression["function"],
                        "context": parsed_expression
                    }

            for idx in range(0,len(typemap)):
                if self.typematch(types,typemap[idx][1:]):
                    parsed_expression["type"] = typemap[idx][0]
                    return None

            # no type match
            if "operator" in parsed_expression:
                return {
                    "error_type": "operator_type_error",
                    "operator": parsed_expression["operator"],
                    "types": types,
                    "context": parsed_expression
                }
            else:
                return {
                    "error_type": "function_type_error",
                    "function": parsed_expression["function"],
                    "types": types,
                    "context": parsed_expression
                }
