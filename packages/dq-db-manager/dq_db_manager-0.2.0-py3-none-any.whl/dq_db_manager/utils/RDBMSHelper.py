import json

def extract_details(executor, query, model_class, return_as_dict: bool = False, *params) -> list:
    print(f"EXECUTING: {query}\nPARAMS: {params}")
    raw_data = executor(query, params)
    # raw_data is already a list of dictionaries from the connection handler
    data_objects = [model_class(**row) for row in raw_data]
    if return_as_dict:
        return [dict(json.loads(data_object.model_dump_json())) for data_object in data_objects]
    else:
        return data_objects

def add_table_to_query(query, params, table_name, alias="table_name", placeholder="%s"):
    query += f"AND {alias} = {placeholder}"
    params.append(table_name)
    return query, params

def add_index_to_query(query, params, index_name, alias="index_name", placeholder="%s"):
    query += f"AND {alias} = {placeholder}"
    params.append(index_name)
    return query, params

def add_view_to_query(query, params, view_name, alias="view_name", placeholder="%s"):
    query += f"AND {alias} = {placeholder}"
    params.append(view_name)
    return query, params

def add_trigger_to_query(query, params, trigger_name, alias="trigger_name", placeholder="%s"):
    query += f"AND {alias} = {placeholder}"
    params.append(trigger_name)
    return query, params

def create_data_source_id(connection_details):
    # user@host:port
    return f"{connection_details['user']}@{connection_details['host']}:{connection_details['port']}"