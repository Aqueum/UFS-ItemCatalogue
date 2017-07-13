from flask import Flask, render_template
app = Flask(__name__)


# render index.html at root
@app.route("/")
def index():
    return render_template('index.html')

# run flask development server
if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
