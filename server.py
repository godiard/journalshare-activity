
import SimpleHTTPServer
import SocketServer
import os

os.chdir('web')

def setup_server():
    PORT = 1097
    Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    httpd = SocketServer.TCPServer(("", PORT), Handler)

    print "serving at port", PORT
    
    return httpd

if __name__ == "__main__":
    server = setup_server()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print "Shutting down server"
        server.shutdown()
