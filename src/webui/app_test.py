# 最小限のテストapp
from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def index():
    return "Home works!"


@app.route("/settings")
def settings():
    return render_template("settings.html")


if __name__ == "__main__":
    print("🧪 Test app starting...")
    app.run(host="0.0.0.0", port=8889, debug=False)
