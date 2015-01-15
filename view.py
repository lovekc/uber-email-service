from flask import Flask, request, render_template
from simple_email import send_email

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def send():
    result = send_email(request.form)
    # hide the technical errors for normal email users by just returning a
    # user friendly message
    return render_template('index.html', message = result.message)

if __name__ == '__main__':
    app.run()
