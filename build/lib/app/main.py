from flask import Flask, jsonify, request

__version__ = "1.0.0"


def add(a, b):
    return a + b


def create_app():
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify(status="ok", version=__version__)

    @app.get("/add")
    def add_numbers():
        try:
            a = float(request.args["a"])
            b = float(request.args["b"])
        except (KeyError, ValueError):
            return jsonify(error="query params a and b must be numbers"), 400
        return jsonify(result=add(a, b))

    @app.get("/greet/<name>")
    def greet(name):
        return jsonify(message=f"Hello, {name}!")

    return app


def run():
    create_app().run(host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run()
