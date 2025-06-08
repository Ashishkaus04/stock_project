#!/usr/bin/env bash
cd src
waitress-serve --host=0.0.0.0 --port=$PORT app.api.app:create_app --call 