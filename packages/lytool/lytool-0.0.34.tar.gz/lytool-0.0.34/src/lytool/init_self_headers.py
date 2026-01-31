def data_in_to_headers(headers, **kwargs):
    for key,value in kwargs.items():
        if '_' in key:
            key = key.replace('_', '-')
        headers[key] = value
    return headers