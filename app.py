from flask import Flask
from flask_cors import CORS
import pymongo
import pymongo.errors


app = Flask(__name__)
CORS(app)
app.secret_key = '1058964416'  
app.config['UPLOAD_FOLDER'] = './static/img'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

miconexion = pymongo.MongoClient('mongodb://localhost:27017')
baseDatos = miconexion["Tienda2"]
usuarios = baseDatos["Usuarios"]
productos = baseDatos["Productos1"]


if __name__ == "__main__":
    from controllers.usuarioController  import *
    from controllers.productosController import *
    app.run(port=3000, debug=True)
