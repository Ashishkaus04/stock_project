#!/usr/bin/env bash
waitress-serve --host=0.0.0.0 --port=$PORT src.app.wsgi:application 