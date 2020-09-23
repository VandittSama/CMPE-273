import logging
from functools import wraps

from flask import Response, make_response, request
from werkzeug.http import parse_date


def check_empty_iterator(iterator, message="Iterator was not empty"):
    try:
        next(iterator)
    except StopIteration:
        pass
    else:
        raise RuntimeError(message)


def etag_cache(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        response = None
        gen = func(*args, **kwargs)

        # Get the caching headers from the view function
        headers = next(gen)
        # Check for ETag caching
        etag = headers.pop('ETag', None)
        if etag in request.if_none_match:
            response = Response(status=304)

        # No valid caching found, so get the real response
        if response is None:
            response = make_response(next(gen))
            check_empty_iterator(gen, "ETag view generator had not finished")

        # Set the caching headers
        if etag:
            response.set_etag(etag)
        for key, value in headers.items():
            response.headers[key] = value

        return response

    return wrapper