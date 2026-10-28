import http.server
import os
import sys

PORT = 3457
DIST_DIR = os.path.join(os.path.dirname(__file__), 'dist')

class SPAHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIST_DIR, **kwargs)
    
    def do_GET(self):
        # Check if the path has a file extension (static asset)
        path = self.path.split('?')[0]
        file_path = os.path.join(DIST_DIR, path.lstrip('/'))
        
        if os.path.isfile(file_path):
            # Serve the file directly
            return super().do_GET()
        
        # For all other routes, serve index.html (SPA fallback)
        self.path = '/index.html'
        return super().do_GET()
    
    def log_message(self, format, *args):
        pass  # Suppress logs

if __name__ == '__main__':
    with http.server.HTTPServer(('0.0.0.0', PORT), SPAHandler) as httpd:
        print(f'Serving CREWINTEL Mobile on http://localhost:{PORT}')
        httpd.serve_forever()
