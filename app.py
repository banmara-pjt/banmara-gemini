from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello, Render! (updated)"

@app.route("/about")
def about():
    return "This is the about page."

@app.route("/json")
def json_page():
    return jsonify({"message": "Hello from JSON!", "status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
