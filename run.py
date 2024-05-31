from app import app

app.secret_key = 'your_secret_key'  # Needed for session management
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=True)
