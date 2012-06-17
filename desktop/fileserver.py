from flask import Flask, Response

app = Flask(__name__)

BUFFER_SIZE = 5000000

paths = []

@app.route('/files/<path:path>')
def get_file(path):
    # TODO: sanitize paths
    try:
        #print path
        f = open('/' + path, 'r')
    except:
        return "File not found"

    def file_piece():
        data = f.read(BUFFER_SIZE)
        while data:
            yield data
            data = f.read(BUFFER_SIZE)

    return Response(file_piece(), mimetype='application/octet-stream')

@app.route('/list')
def get_listing():
    return '\r\n'.join(paths)

def setup_test():
    paths.append('/Users/juan/Desktop/IMG_0343.JPG')
    paths.append('/Users/juan/Desktop/LivingSocial Voucher.pdf')

if __name__ == '__main__':
    setup_test()
    app.run(host='0.0.0.0')
