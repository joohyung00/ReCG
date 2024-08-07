from copy import deepcopy
import json

import random
from pprint import pprint

import sys
sys.path.insert(1, '/root/VLDB2024_ReCG/Experiment')
from load_json import load_dataset, load_schema

global neg_schema_dict

# Input
#
# Target dict :=
# {
#    operation : {
#                 nesting_level_1: [path1 , path2 , ..., path3 ],
#                 nesting_level_2: [path10, path20, ..., path30]
#    ...
# }
# path := [key1, key2, ..., key_n] 

global NEW_SCHEMA_FROM
global NEW_KEY_FROM
global words


def generate_negative_schema(goal_schema, operation, path, new_schema, new_key):

    global NEW_SCHEMA_FROM
    global NEW_KEY_FROM

    NEW_SCHEMA_FROM = new_schema
    NEW_KEY_FROM = new_key

    if operation == "change_type":
        return neg_change_type(goal_schema, path)

    # Arrays
    if operation == "array_tuple_add":
        return neg_array_tuple_add(goal_schema, path)
    if operation == "array_tuple_delete":
        return neg_array_tuple_delete(goal_schema, path)
    if operation == "array_collection_anyOf":
        return neg_array_collection_anyOf(goal_schema, path)
    if operation == "array_collection_single":
        return neg_array_collection_single(goal_schema, path)
    
    # Objects
    if operation == "object_delete_required_property":
        return neg_object_delete_required_property(goal_schema, path)
    if operation == "object_add_property":
        return neg_object_add_property(goal_schema, path)

    # Composition
    if operation == "anyOf_object_collection":
        return neg_anyOf_object_collections(goal_schema, path)
    if operation == "anyOf_object_tuple":
        return neg_anyOf_object_tuples(goal_schema, path)
    if operation == "anyOf_object_tuple_collection":
        schema = neg_anyOf_object_tuple_collection(goal_schema, path)
        return schema
    if operation == "anyOf_array_collection":
        return neg_anyOf_array_collection(goal_schema, path)





####################################################################################
################################### Changing types ####################################
####################################################################################

def neg_change_type(goal_schema, path):

    def return_integer(number):
        return random.choice( [i + 1 for i in range(number)] )

    def change_type(goal_schema, target, path):

        global NEW_SCHEMA_FROM

        new_schema = get_random_subschema(goal_schema, path)

        return new_schema

    return neg_template(change_type, "change_type", goal_schema, path)




##############################################################################
################################### ARRAY ####################################
##############################################################################


def neg_array_tuple_add(goal_schema, path):
    
    global NEW_SCHEMA_FROM

    def add_element(goal_schema, target, path):

        if NEW_SCHEMA_FROM == "schema":
            to_add = get_random_subschema(goal_schema, path)
        elif  NEW_SCHEMA_FROM == "same_schema":
            # To change NEW_SCHEMA_FROM
            to_add = get_same_subschema(goal_schema, path)
        elif NEW_SCHEMA_FROM == "random":
            to_add = generate_random_schema()

        # target["items"].insert(random.randint(0, len(goal_schema["items"])), to_add)
        if "items" in target:
            target["items"].append(target["items"][-1])
        elif "prefixItems" in target:
            target["prefixItems"].append(target["prefixItems"][-1])

        return target

    return neg_template(add_element, "array_tuple_add", goal_schema, path)


def neg_array_tuple_delete(goal_schema, path):

    def delete_subschema(goal_schema, target, path):
        copied = deepcopy(target)
        
        if "items" in copied:
            copied["items"].pop(random.randrange(len(copied["items"])))
        elif "prefixItems" in copied:
            copied["prefixItems"].pop(random.randrange(len(copied["prefixItems"])))

        if "maxItems" in copied:
            copied["maxItems"] = copied["maxItems"] - 1
        if "minItems" in copied:
            copied["minItems"] = copied["minItems"] - 1

        return copied

    return neg_template(delete_subschema, "array_tuple_delete", goal_schema, path)


def neg_array_collection_anyOf(goal_schema, path):
    
    def items_new_subschema(goal_schema, target, path):
        global NEW_SCHEMA_FROM

        if NEW_SCHEMA_FROM == "schema":
            to_add = get_random_subschema(goal_schema, path)
        elif  NEW_SCHEMA_FROM == "same_schema":
            to_add = get_same_subschema(goal_schema, path)
        elif NEW_SCHEMA_FROM == "random":
            existing_types = set()

            for subschema in target["items"]["anyOf"]:
                try:
                    existing_types.add(subschema["type"])
                except KeyError:
                    continue

            to_add = generate_unexisting_schema(existing_types)

        target["items"]["anyOf"].append(to_add)
        
        if "allOf" not in target:
            target["allOf"] = []

        target["allOf"].append({"contains": to_add})

        return target

    return neg_template(items_new_subschema, "array_collection_anyOf", goal_schema, path)


def neg_array_collection_single(goal_schema, path):
    
    def single_to_anyOf(goal_schema, target, path):
        global NEW_SCHEMA_FROM

        if NEW_SCHEMA_FROM == "schema":
            to_add = get_random_subschema(goal_schema, path)
        elif  NEW_SCHEMA_FROM == "same_schema":
            to_add = get_random_subschema(goal_schema, path)
        elif NEW_SCHEMA_FROM == "random":

            existing_types = set()
            existing_types.add(target["type"])

            to_add = generate_unexisting_schema(existing_types)

        target["items"] = {"anyOf": [target["items"], to_add]}

        return target

    return neg_template(single_to_anyOf, "array_collection_single", goal_schema, path)


###############################################################################
################################### OBJECT ####################################
###############################################################################




def neg_object_delete_required_property(goal_schema, path):
    
    def delete_required_property(goal_schema, target, path):

        to_delete = target["required"].pop(random.randrange(len(target["required"])))

        if "not" not in target.keys():
            target["not"] = {"required": [to_delete]}
        else:
            if "required" not in target["not"].keys():
                target["not"] = {"required": [to_delete]}
            else:
                target["not"]["required"].append(to_delete)

        return target

    return neg_template(delete_required_property, "object_delete_required_property", goal_schema, path)


def neg_object_add_property(goal_schema, path):

    global NEW_SCHEMA_FROM
    global NEW_KEY_FROM

    def add_property(goal_schema, target, path):
        if "properties" not in target:
            target["properties"] = {}

        if NEW_SCHEMA_FROM == "schema":
            adding_schema = get_random_subschema(goal_schema, "ANY")
        elif NEW_SCHEMA_FROM == "same_schema":
            adding_schema = get_random_subschema(goal_schema, "ANY")
        elif NEW_SCHEMA_FROM == "random":
            adding_schema = generate_random_schema()

        if NEW_KEY_FROM == "schema":
            try:
                adding_key = get_existing_key(goal_schema, path)
            except IndexError:
                adding_key = generate_random_string()
        elif NEW_KEY_FROM == "random":
            adding_key = generate_random_string()
        else:
            adding_key = generate_random_string()

        target["properties"][adding_key] = adding_schema

        if "required" in target:
            target["required"].append(adding_key)
        else:
            target["required"] = [adding_key]

        return target

    return neg_template(add_property, "object_add_property", goal_schema, path)
    


####################################################################################
################################### COMPOSITION ####################################
####################################################################################

def neg_anyOf_object_collections(goal_schema, path):

    def generalize_objects(goal_schema, target, path):

        def merge_object_collections(objCol1, objCol2):
            col1 = objCol1["additionalProperties"]
            col2 = objCol2["additionalProperties"]

            new_object = {"type": "object",
                        "additionalProperties": {"anyOf": [col1, col2]}}
            
            return new_object

        target_indices = []

        subschemas = target["anyOf"]

        for i, subschema in enumerate(subschemas):
            try:
                if subschema["type"] == "object" and "additionalProperties" in subschema and subschema["additionalProperties"] != False:
                    target_indices.append(i)
            except:
                pass
        
        to_merge = random.sample(target_indices, 2)

        subschema1 = subschemas[to_merge[0]]
        subschema2 = subschemas[to_merge[1]]

        merged = merge_object_collections(subschema1, subschema2)

        new_subschemas = []

        # Generate new subschemas
        for i, subschema in enumerate(subschemas):
            if i not in to_merge:
                new_subschemas.append(subschema)
        new_subschemas.append(merged)

        return {"anyOf": new_subschemas}

    
    return neg_template(generalize_objects, "anyOf_object_collection", goal_schema, path)


def neg_anyOf_object_tuples(goal_schema, path):

    def generalize_objects(goal_schema, target, path):

        def merge_object_tuples(objTup1, objTup2):

            # Properties
            properties1 = objTup1["properties"]
            properties2 = objTup2["properties"]

            new_properties = {**properties1, **properties2}

            # Requireds

            try:
                required1 = objTup1["required"]
            except:
                required1 = []
            try:
                required2 = objTup2["required"]
            except:
                required2 = []
            new_required = list(set(required1) & set(required2))

            new_object = {
                "type": "object",
                "additionalProperties": False,
                "properties": new_properties, 
                "required": new_required
            }
            
            return new_object


        target_indices = []

        subschemas = target["anyOf"]

        for i, subschema in enumerate(subschemas):
            try:
                if subschema["type"] == "object":
                    if "additionalProperties" in subschema and subschema["additionalProperties"] == False:
                        target_indices.append(i)
                    if "additionalProperties" not in subschema:
                        target_indices.append(i)
            except:
                pass
        
        to_merge = random.sample(target_indices, 2)

        subschema1 = subschemas[to_merge[0]]
        subschema2 = subschemas[to_merge[1]]

        merged = merge_object_tuples(subschema1, subschema2)

        new_subschemas = []

        # Generate new subschemas
        for i, subschema in enumerate(subschemas):
            if i not in to_merge:
                new_subschemas.append(subschema)
        new_subschemas.append(merged)

        return {"anyOf": new_subschemas}
    
    return neg_template(generalize_objects, "anyOf_object_tuple", goal_schema, path)


def neg_anyOf_object_tuple_collection(goal_schema, path):

    def generalize_objects(goal_schema, target, path):

        def merge_object_tuple_collection(objTup, objCol):
            to_return = deepcopy(objTup)
            to_return["additionalProperties"] = objCol["additionalProperties"]
            
            return to_return

        collection_indices = []
        tuple_indices = []

        subschemas = target["anyOf"]

        for i, subschema in enumerate(subschemas):
            if "type" in subschema:
                if subschema["type"] == "object" and "additionalProperties" in subschema and subschema["additionalProperties"] != False:
                    collection_indices.append(i)
                if subschema["type"] == "object":
                    if "additionalProperties" in subschema and subschema["additionalProperties"] == False:
                        tuple_indices.append(i)
                    if "additionalProperties" not in subschema:
                        tuple_indices.append(i)
            
        

        to_merge_tup_idx  = random.sample(tuple_indices, 1)[0]
        to_merge_coll_idx = random.sample(collection_indices, 1)[0]
        
        to_merge_tup = subschemas[to_merge_tup_idx]
        to_merge_coll = subschemas[to_merge_coll_idx]

        return merge_object_tuple_collection(to_merge_tup, to_merge_coll)

    
    return neg_template(generalize_objects, "anyOf_object_tuple_collection", goal_schema, path)

def neg_anyOf_array_collection(goal_schema, path):
    
    
    def generalize_arrays(goal_schema, target, path):

        def merge_arrays(array1, array2):
        # Assumptions! Only arrayCollection

            items1 = array1["items"]
            items2 = array2["items"]

            new_array = {"type": "array",
                        "items": {"anyOf": [items1, items2]}}
            
            return new_array

        target_indices = []

        subschemas = target["anyOf"]

        for i, subschema in enumerate(subschemas):
            try:
                if subschema["type"] == "array" and "items" in subschema and type(subschema["items"]) is dict:
                    target_indices.append(i)
            except:
                pass
        
        to_merge = random.sample(target_indices, 2)

        subschema1 = subschemas[to_merge[0]]
        subschema2 = subschemas[to_merge[1]]

        merged = merge_arrays(subschema1, subschema2)

        new_subschemas = []

        # Generate new subschemas
        for i, subschema in enumerate(subschemas):
            if i not in to_merge:
                new_subschemas.append(subschema)
        new_subschemas.append(merged)

        return {"anyOf": new_subschemas}

    return neg_template(generalize_arrays, "anyOf_array_collection", goal_schema, path)










#####################################################################################
################################### subfunctions ####################################
#####################################################################################

def neg_template(function, operation, goal_schema, path):

    new_schema = deepcopy(goal_schema)

    target = locate_subschema(new_schema, path)

    updated_schema = function(goal_schema, target, path)

    negative_schema = update(new_schema, path, updated_schema)

    return negative_schema


def define_or_concatenate(dictionary, key, somelist):
    if key not in dictionary:
        dictionary[key] = somelist
    else:
        dictionary[key] = dictionary[key] + somelist


def generate_random_schema():

    sample_list = [
        {"type": "string"},
        {"type": "number"},
        {"type": "boolean"},
        {"type": "null"},
        {"type": "array"},
        {"type": "object"}
    ]

    return random.choice(sample_list)


def generate_random_string():

    words = []
    with open("random_words.txt", "r") as file_:
        for line in file_:
            words.append(line.strip())

    return random.choice(words)


def generate_unexisting_schema(type_set):

    type_to_schema = {
        "string": {"type": "string"},
        "number": {"type": "number"},
        "boolean": {"type": "boolean"},
        "null": {"type": "null"},
        "array": {"type": "array"},
        "object": {"type": "object"}
    }

    print(type_set)

    for type_ in type_set:
        del type_to_schema[type_]
    
    return random.choice(list(type_to_schema.values()))


def get_random_subschema(schema, finding_path):
    import collections

    def probe_json(current_path, path_list, json_object):
        if type(json_object) is list:
            for i, subschema in enumerate(json_object):
                copied_path = deepcopy(current_path)
                copied_path.append(i)
                probe_json(copied_path, path_list, subschema)
            return

        elif type(json_object) is dict:
            keys = json_object.keys()
            if "type" in keys:
                path_list.append(current_path)
            for key in keys:
                copied_path = deepcopy(current_path)
                copied_path.append(key)
                probe_json(copied_path, path_list, json_object[key])
            return
        return
    
    path_list = []
    probe_json([], path_list, schema)

    if finding_path == "ANY":
        return deepcopy(locate_subschema(schema, random.choice(path_list)))


    filtered_pathlist = []
    for path in path_list:
        if collections.Counter(path[:-1]) != collections.Counter(finding_path):
            filtered_pathlist.append(path)

    return deepcopy(locate_subschema(schema, random.choice(filtered_pathlist)))

def get_same_subschema(schema, finding_path):
    pass

def get_existing_key(schema, finding_path):

    def probe_json(key_set, json_object):
        if type(json_object) is list:
            for subschema in json_object:
                probe_json(key_set, subschema)
            return
        elif type(json_object) is dict:
            keys = json_object.keys()
            if "type" in keys and json_object["type"] == "object":
                if "properties" in json_object:
                    key_set.update(set(json_object["properties"].keys()))
            for key in keys:
                probe_json(key_set, json_object[key])
            return
        return

    # Get all keys in JSON schema
    key_set = set()
    probe_json(key_set, schema)
    
    # Filter keys
    filtered_keylist = []
    target_schema = locate_subschema(schema, finding_path)

    try:
        to_filter = target_schema["properties"].keys()
    except KeyError:
        to_filter = []

    for string in key_set:
        if string not in to_filter:
            filtered_keylist.append(string)

    # Return among filtered keys
    return random.choice(filtered_keylist)


def update(schema, path, new_target):
    if not path:
        return deepcopy(new_target)
    
    parent = locate_subschema(schema, path[:-1])
    parent[path[-1]] = new_target

    return schema


def locate_subschema(schema, path):
    for step in path:
        schema = schema[step]
        
    return schema