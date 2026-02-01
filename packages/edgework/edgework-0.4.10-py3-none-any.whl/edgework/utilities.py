import re


def camel_to_snake(name):
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def dict_camel_to_snake(data):
    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            new_key = camel_to_snake(k)
            new_dict[new_key] = (
                dict_camel_to_snake(v) if isinstance(v, (dict, list)) else v
            )
        return new_dict
    elif isinstance(data, list):
        return [dict_camel_to_snake(item) for item in data]
    else:
        return data
