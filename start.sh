#!/usr/bin/env bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
waitress-serve --host=0.0.0.0 --port=$PORT src.app.api.app:app 