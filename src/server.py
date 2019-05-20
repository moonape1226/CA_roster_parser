import os

from flask import Flask, render_template

app = Flask(__name__, static_url_path='/static')

@app.route("/")
def hello_index():
    print(os.getcwd())
    return render_template('index.html')

@app.route('/parse', methods=['POST'])
def parse():
    # do the parse thing
    return "this is parse result"

if __name__ == "__main__":
    app.run()
