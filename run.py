from app import app, serverGeneral

if __name__ == '__main__':
    serverGeneral.daemon = True
    serverGeneral.start()
    app.run(port=5000)

    
    