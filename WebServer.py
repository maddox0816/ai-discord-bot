from flask import Flask, render_template, send_from_directory   
from threading import Thread
app = Flask('')

@app.route('/')
def main():
    return "Chatbot is online"







def run():
    app.run(host="0.0.0.0", port=8080)


def start():
    server = Thread(target=run)
    server.start()