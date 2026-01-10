from firebase_functions import https_fn
from flask import Flask
from app import app as flask_app

@https_fn.on_request()
def app(req: https_fn.Request) -> https_fn.Response:
    with flask_app.request_context(req.environ):
        return flask_app.full_dispatch_request()
