from app import app, productos
from flask import request, jsonify, redirect, render_template, session
import pymongo
import pymongo.errors
import os
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId

@app.route("/listarProductos")
def listar_productos():
    if "user" in session:
        try:
            lista_productos = productos.find()
            return render_template("listar.html", productos=lista_productos)
        except pymongo.errors.PyMongoError as error:
            return render_template("listar.html", mensaje=str(error))
    return render_template("formLogin.html", mensaje="Debe primero ingresar con sus credenciales")

@app.route("/agregar", methods=['POST', 'GET'])
def agregar():
    if "user" in session:
        if request.method == 'POST':
            return _agregar_producto()
        return render_template("agregar.html")
    return render_template("formLogin.html", mensaje="Debe primero ingresar con sus credenciales")

def _agregar_producto():
    try:
        codigo = int(request.form['txtCodigo'])          
        nombre = request.form['txtNombre']
        precio = int(request.form['txtPrecio'])
        categoria = request.form['cbCategoria']
        foto = request.files['fileFoto']
        nombre_foto = f"{codigo}.{secure_filename(foto.filename).rsplit('.', 1)[1].lower()}"
        
        if not existe_producto(codigo):   
            producto = {"codigo": codigo, "nombre": nombre, "precio": precio, 
                        "categoria": categoria, "foto": nombre_foto}
            if productos.insert_one(producto).acknowledged:
                foto.save(os.path.join(app.config["UPLOAD_FOLDER"], nombre_foto))
                return redirect('/listarProductos')
            return render_template("agregar.html", mensaje="Problemas al agregar el producto.")
        return render_template("agregar.html", mensaje="Ya existe un producto con ese código")
    except pymongo.errors.PyMongoError as error:
        return render_template("agregar.html", mensaje=str(error))

@app.route("/consultar/<string:id>", methods=["GET"])
def consultar(id):
    if "user" in session:
        try:
            producto = productos.find_one({"_id": ObjectId(id)})
            if producto:
                return render_template("frmActualizarProducto.html", producto=producto)
            else:
                return redirect("/listarProductos")  
        except pymongo.errors.PyMongoError:
            return redirect("/listarProductos")
    return render_template("formLogin.html", mensaje="Debe primero ingresar con sus credenciales")


def existe_producto(codigo):    
    return productos.find_one({"codigo": codigo}) is not None

@app.route("/actualizar", methods=["POST"])
def actualizar_producto():
    if "user" in session:
        producto = {} 
        try:
            id = ObjectId(request.form["id"])  
            codigo = int(request.form["txtCodigo"])  
            
            
            nombre = request.form.get("txtNombre", "")  
            precio = int(request.form.get("txtPrecio", 0))  
            categoria = request.form.get("cbCategoria", "")    
            foto = request.files.get("fileFoto")  
            nombre_foto = None
            
            if foto and foto.filename:  
                nombre_foto = f"{codigo}.{secure_filename(foto.filename).rsplit('.', 1)[1].lower()}"
    
            producto = {
                "nombre": nombre,
                "precio": precio,
                "categoria": categoria,
                "_id": id,  
            }
            if nombre_foto:
                producto['foto'] = nombre_foto  
            
           
            if not productos.find_one({"codigo": codigo, "_id": {"$ne": id}}):
               
                productos.update_one({"_id": id}, {"$set": producto})

                if nombre_foto:  
                    foto.save(os.path.join(app.config["UPLOAD_FOLDER"], nombre_foto))
                
                return redirect("/listarProductos")
            else:
                return render_template("actualizar.html", producto=producto, mensaje="Producto ya existe con ese código.")
        except pymongo.errors.PyMongoError:
            return redirect("/listarProductos")
        except Exception as e:
            
            return render_template("actualizar.html", mensaje=str(e), producto=producto)
    
    return render_template("formLogin.html", mensaje="Debe primero ingresar con sus credenciales")




@app.route("/eliminar/<string:id>", methods=["POST"])
def eliminar(id):
    if "user" in session:
        try:
            criterio = {"_id": ObjectId(id)}
            producto = productos.find_one(criterio)
            if producto and productos.delete_one(criterio).acknowledged:
                if producto['foto']:
                    ruta_foto = os.path.join(app.config['UPLOAD_FOLDER'], producto['foto'])
                    if os.path.exists(ruta_foto):
                        os.remove(ruta_foto)
        except pymongo.errors.PyMongoError:
            pass
        return redirect("/listarProductos")
    
    return render_template("formLogin.html", mensaje="Debe primero ingresar con sus credenciales") 


@app.route("/api/listarProductos", methods=["GET"])
def api_listar_productos():
    lista = [{"_id": str(p['_id']), "codigo": p['codigo'], "nombre": p['nombre'], 
              "precio": p['precio'], "categoria": p['categoria'], "foto": p['foto']} for p in productos.find()]
    return jsonify({'productos': lista})

@app.route("/api/consultar/<string:id>", methods=["GET"])
def api_consultar(id):
    producto = productos.find_one({"_id": ObjectId(id)})
    return jsonify({'producto': {"_id": str(producto['_id']), "codigo": producto['codigo'], 
                                 "nombre": producto['nombre'], "precio": producto['precio'], 
                                 "categoria": producto['categoria'], "foto": producto['foto']}})

@app.route("/api/agregar", methods=["POST"])
def api_agregar():
    try:
        codigo = int(request.json['codigo'])          
        nombre = request.json['nombre']
        precio = int(request.json['precio'])
        categoria = request.json['categoria']
        foto = request.json['foto']

        if not existe_producto(codigo):   
            productos.insert_one({
                "codigo": codigo, "nombre": nombre, "precio": precio, 
                "categoria": categoria, "foto": foto
            })
            return jsonify({"mensaje": "Producto agregado correctamente."})
        
        return jsonify({"mensaje": f"Ya existe un producto con el código {codigo}"})
    except pymongo.errors.PyMongoError as error:
        return jsonify({"mensaje": str(error)})
