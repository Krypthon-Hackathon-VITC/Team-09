from app import app

debug = True

if __name__ == "__main__":
    app.run('0.0.0.0', 5000, debug=debug)