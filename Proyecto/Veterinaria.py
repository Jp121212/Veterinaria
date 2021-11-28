
from flask import Flask, request, jsonify, Blueprint
from flask_jwt_extended.utils import create_access_token, create_refresh_token, get_jwt_identity
from flask_jwt_extended.view_decorators import jwt_required
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api
from sqlalchemy.orm import backref
from werkzeug.security import check_password_hash,generate_password_hash
from flask_jwt_extended import JWTManager, jwt_manager


app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "super-secret"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost:3306/veterinaria_jp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
api = Api(app)

auth = Blueprint("auth", __name__, url_prefix="/api/v1/auth")
ruta = Blueprint("ruta",__name__,url_prefix="/api/v2/ruta")
##BASE DE DATOS
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.Text(), nullable=False)
    def __repr__(self) -> str:
        return 'User>>> {self.username}'

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), unique=True, nullable=False)
    cedula = db.Column(db.String(80), unique=True, nullable=False)
    direccion = db.Column(db.String(200), nullable=False)
    numero = db.Column(db.String(30),nullable=False)
    pets = db.relationship('Pet', backref = 'owner' )
    def repr(self) :
        return "[Cliente %s]" % str(self.id)

class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    raza = db.Column(db.String(80),nullable=False)
    peso = db.Column(db.Float(10),nullable=False)
    tamano = db.Column(db.String(80),nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("cliente.id")) 
    citas = db.relationship("Citas",backref= 'owner')  

class Especialidad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    doc = db.relationship("Doctor",backref = "especialidad")
    def repr(self) :
        return "Especialidad %s" % str(self.id)

class Doctor(db.Model):
     id = db.Column(db.Integer, primary_key=True)
     nombre = db.Column(db.String(80), unique=True, nullable=False)
     Codigo_unico = db.Column(db.String(80), unique=True, nullable=False)
     numero = db.Column(db.String(30),nullable=False)
     especialidad_id = db.Column(db.Integer, db.ForeignKey("especialidad.id"))
     cits = db.relationship("Citas",backref = "owner_Hora") 
     hora = db.relationship("Citas",backref = "owner_horaunica")
     def repr(self) :
        return "Doctor %s" % str(self.id)

class Citas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    paciente = db.Column(db.Integer, db.ForeignKey("pet.id"))
    procedimiento = db.Column(db.String(100),nullable=False)
    doctor_id = db.Column(db.Integer,db.ForeignKey("doctor.id"))
    dia = db.Column(db.String(50),nullable=False)
    Hora = db.Column(db.String(80), unique=True, nullable=False)

db.create_all()       

##LOGICA AUTENTICACION
@auth.post('/signup')
def register():
    username = request.json['username']
    email = request.json['email']
    password = request.json['password']

    if len(password)<6:
        return jsonify({
            "error": 'Password es muy corta :c'
        }),400

    if len(username)<3:
        return jsonify({
            "error": 'Nombre de usuario es muy corto :c'
        }),400

    if User.query.filter_by(email=email).first() is not None:
        return jsonify({"error": "Email ya esta tomado"}),409
    if User.query.filter_by(username=username).first() is not None:
        return jsonify({"error": "Email ya esta tomado"}),409

    pwd_hash=generate_password_hash(password)
    user=User(username=username,password=pwd_hash, email=email)
    db.session.add(user)
    db.session.commit()
    return jsonify({
        "Mensaje": "Usuario creado",
        "usario":{
            'username':username, "email": email
        }
    }),201

@auth.post('/login')
def login():
    email = request.json.get('email', '')
    password = request.json.get('password', '')

    user = User.query.filter_by(email=email).first()

    if user:
        is_pass_correct = check_password_hash(user.password, password)

        if is_pass_correct:
            refresh = create_refresh_token(identity=user.id)
            access = create_access_token(identity=user.id)

            return jsonify({
                'user': {
                    'refresh': refresh,
                    'access': access,
                    'username': user.username,
                    'email': user.email
                }

            }), 200

    return jsonify({'error': 'Credenciales incorrectas'}), 401

@auth.post("/token/refresh")
@jwt_required(refresh=True) 
def refresh_users_token():
   identity = get_jwt_identity()
   access = create_access_token(identity=identity)
   return jsonify({
       "Nuevo Token generado": ":)",
       "access": access
   }),200

@auth.get("/me")
@jwt_required()
def me():
    return {"user": "me"}

@auth.post("/recover-password")
def recoverpass():
    email = request.json.get('email', '')
    user = User.query.filter_by(email=email).first()
    if user == None:
        return jsonify({"Error":"Email no registrado"}),409
    else:
        return jsonify({"Email encontrado": "Su codigo de verificacion para restablecer la contrasena fue enviado al correo:  " + (email)}),201


##POST CLIENTE
@auth.post("/cliente")
@jwt_required()
def register1():
    nombre = request.json['nombre']
    cedula = request.json['cedula']
    direccion = request.json['direccion']
    numero = request.json['numero']
    if len(cedula)<13:
        return jsonify({
            "error": 'Cedula tiene que ser menor a 13 caracteres :c'
        }),400

    if len(nombre)<3:
        return jsonify({
            "error": 'Indique su nombre con almenos un apellido :c'
        }),400

    if Cliente.query.filter_by(cedula=cedula).first() is not None:
        return jsonify({"error": "El numero de cedula ya tiene un registro"}),409
    if Cliente.query.filter_by(nombre=nombre).first() is not None:
        return jsonify({"error": "El nombre ya esta registrado"}),409
    
    if len(nombre)== None:
        return jsonify({
            "error": 'Nombre tiene que estar obligatoriamente'
        }),400
    
    if len(cedula)== None:
        return jsonify({
            "error": 'Cedula tiene que estar obligatoriamente'
        }),400


    cliente=Cliente(nombre=nombre,cedula=cedula, direccion=direccion, numero=numero)
    db.session.add(cliente)
    db.session.commit()
    return jsonify({
        "Mensaje": "Cliente creado",
        "usario":{
            'Nombre':nombre, "Numero": numero
        }
    }),201

##POST PET
@auth.post("/pet")
@jwt_required()
def register2():
    nombre = request.json['nombre']
    raza = request.json['raza']
    peso = request.json['peso']
    tamano = request.json['tamano']
    owner_id = request.json['owner_id']
    
    pet= Pet(nombre=nombre,raza=raza,peso=peso,tamano=tamano,owner_id=owner_id)
    db.session.add(pet)
    db.session.commit()
    return jsonify({
        "Mensaje": "Mascota creada",
        "Pet":{
            "nombre": nombre, "raza": raza, "owner_id": owner_id
        }
    }),201

##POST ESPECIALIDAD
@auth.post("/especialidad")
@jwt_required
def register3():
    nombre = request.json['nombre']
    especialidad = Especialidad(nombre=nombre)
    db.session.add(especialidad)
    db.session.commit()
    return jsonify({
        "Mensaje": "Especialidad creada",
        "Especialidad":{
            "Nombre ": nombre
        }
    }),201

##POST DOC
@ruta.post("/doctor")
def ingreso():

    nombre = request.json['nombre']
    Codigo_unico = request.json["Codigo_unico"]
    numero = request.json['numero']
    especialidad_id = request.json['especialidad_id']

    if len(Codigo_unico)<3:
        return jsonify({
            "error": 'CU tiene que ser de 3 caracteres :c'
        }),400
    doctor= Doctor(nombre=nombre,Codigo_unico=Codigo_unico,numero=numero,especialidad_id=especialidad_id)
    db.session.add(doctor)
    db.session.commit()
    return jsonify({
        "Mensaje": "Doctor creado",
        "Doctor":{
            "Nombre": nombre,"Codigo":Codigo_unico, "numero": numero
        }
    }),201

##POST CITA
@ruta.post("/cita")
def ingreso1():
    paciente = request.json['paciente']
    procedimiento = request.json["procedimiento"]
    doctor_id = request.json['doctor_id']
    dia = request.json['dia']
    Hora = request.json['Hora']

    paciente = Citas(paciente=paciente,procedimiento=procedimiento,doctor_id=doctor_id,dia=dia,Hora=Hora)
    db.session.add(paciente)
    db.session.commit()
    return({"response": "Cita registrada exitosamente :)!"}),201



##END POINTS CLIENTE BY ID
class ClienteByID (Resource):
    @jwt_required()
    def get(self,id):
        cliente = Cliente.query.filter_by(id=id).first()
        if cliente == None:
            return ({"Error": "No se encuentran Clientes en la lista con ese id :" + str(id)}),406
        else:
            return{'cliente': {
                "id": cliente.id,
                "nombre": cliente.nombre,
                "cedula": cliente.cedula,
                "direccion": cliente.direccion,
                "numero": cliente.numero,
            }},201
    @jwt_required()
    def put(self,id):
        cliente = Cliente.query.filter_by(id=id).first()
        datos = request.get_json()
        if cliente == None:
            return ({"Error": "No se encuentran Clientes por actualizar en la lista con ese id :" + str(id)}),406
        else:
            cliente.direccion = datos['direccion']
            cliente.numero = datos['numero']
            db.session.commit()
            return({"Registro de Campos actualizados":{
                "direccion: " : cliente.direccion,
                "numero": cliente.numero}
            }),200
    @jwt_required()
    def delete (self,id): 
        cliente = Cliente.query.filter_by(id=id).first()
        if cliente:
            db.session.delete(cliente)
            db.session.commit()
            return { "response": "Cliente con id: {item}. Borrado exitosamente. ".format(item=id)}, 203
        else:
            return ({"Error": "No se encuentran Clientes para borrar en la lista con ese id :" + str(id)}),406

##ENDPOINT PET
class PetByID (Resource):
    @jwt_required()
    def get(self,id):
        pet = Pet.query.filter_by(id=id).first()
        if pet == None:
            return ({"Error": "No se encuentran mascotas en la lista con ese id :" + str(id)}),406
        else:
            return{'Pet': {
                "id": pet.id,
                "nombre": pet.nombre,
                "raza": pet.raza,
                "peso": pet.peso,
                "tamano": pet.tamano,
                "owner_id": pet.owner_id
            }},201
    @jwt_required()
    def put(self,id):
        pet = Pet.query.filter_by(id=id).first()
        datos = request.get_json()
        if pet == None:
            return ({"Error": "No se encuentran Mascotas por actualizar en la lista con ese id :" + str(id)}),406
        else:
            pet.nombre = datos['nombre']
            pet.peso = datos['peso']
            pet.tamano = datos["tamano"]
            db.session.commit()
            return({"Registro de Campos actualizados":{
                "nombre: " : pet.nombre,
                "peso": pet.peso,
                "tamano": pet.tamano}
            }),200
    @jwt_required()
    def delete (self,id): 
        pet = Pet.query.filter_by(id=id).first()
        if pet:
            db.session.delete(pet)
            db.session.commit()
            return { "response": "Mascota con id: {item}. Borrado exitosamente. ".format(item=id)}, 203
        else:
            return ({"Error": "No se encuentran Mascotas para borrar en la lista con ese id :" + str(id)}),406

##ENDPOINT ESCPECIALIDAD
class EspecialidadByID(Resource):
    @jwt_required()
    def get(self,id):
        especialidad = Especialidad.query.filter_by(id=id).first()
        if especialidad == None:
            return ({"Error": "No se encuentran especialidades en la lista con ese id :" + str(id)}),406
        else:
            return{'Especialidad': {
                
                "nombre": especialidad.nombre,
                
            }},201

##ENDPOINT DOCTOR
class DoctorById(Resource):
    @jwt_required()
    def get(self,id):
        doctor = Doctor.query.filter_by(id=id).first()
        if doctor == None:
            return ({"Error": "No se encuentran Doctores en la lista con ese id :" + str(id)}),406
        else:
            return{'Doctor': {
                "id": doctor.id,
                "nombre": doctor.nombre,
                "Codigo_Unico": doctor.Codigo_unico,
                "numero": doctor.numero,
                "especialidad_id": doctor.especialidad_id,
            }},201
    @jwt_required()
    def put(self,id):
        doctor = Doctor.query.filter_by(id=id).first()
        datos = request.get_json()
        if doctor == None:
            return ({"Error": "No se encuentran Doctores por actualizar en la lista con ese id :" + str(id)}),406
        else:
            doctor.numero = datos['numero']
            db.session.commit()
            return({"Registro de Campos actualizados":{
                "numero: " : doctor.nombre,
                }
            }),200
    @jwt_required()
    def delete (self,id): 
        doctor = Doctor.query.filter_by(id=id).first()
        if doctor:
            db.session.delete(doctor)
            db.session.commit()
            return { "response": "Doctor con id: {item}. Borrado exitosamente. ".format(item=id)}, 203
        else:
            return ({"Error": "No se encuentran Doctores para borrar en la lista con ese id :" + str(id)}),406

##ENDPOINT CITA
class CitaByID(Resource):
    @jwt_required
    def get(self,id):
        cita = Citas.query.filter_by(id=id).first()
        if cita == None:
            return ({"Error": "No se encuentran Citas en la lista con ese id :" + str(id)}),406
        else:
            return{'Citas': {
                "id": cita.id,
                "paciente": cita.paciente,
                "procedimiento": cita.procedimiento,
                "Doctor_id": cita.doctor_id,
                "Dia": cita.dia,
                "Hora": cita.Hora
            }},201
    @jwt_required()
    def put(self,id):
        cita = Citas.query.filter_by(id=id).first()
        datos = request.get_json()
        if cita == None:
            return ({"Error": "No se encuentran citas por actualizar en la lista con ese id :" + str(id)}),406
        else:
            cita.procedimiento = datos['procedimiento']
            cita.dia = datos['dia']
            cita.hora = datos ['Hora']
            cita.doctor_id= datos ['doctor_id']
            db.session.commit()
            return({"Registro de Campos actualizados":":)"
                }),200
    @jwt_required()
    def delete (self,id): 
        cita = Citas.query.filter_by(id=id).first()
        if cita:
            db.session.delete(cita)
            db.session.commit()
            return { "response": "Cita con id: {item}. Borrado exitosamente. ".format(item=id)}, 203
        else:
            return ({"Error": "No se encuentran Citas para borrar en la lista con ese id :" + str(id)}),406

##ENDPOINT EMAILCHANGE      
class UserByEmail(Resource):

    def put(self,email):
        user = User.query.filter_by(email=email).first()
        datos = request.get_json()
        if user == None:
            return ({"Error": "Email no registrado, verifique de nuevo"}),403
        else:
            user.password = datos['password']
            user.password=generate_password_hash(user.password) 
            user=User(password=user.password) 
            db.session.commit()
            return {"response": "Password Actualizada correctamente"},200


##RUTAS DISP
app.register_blueprint(ruta)
app.register_blueprint(auth)
api.add_resource(CitaByID, '/get-cita/<int:id>')
api.add_resource(DoctorById, '/get-doctor/<int:id>')
api.add_resource(UserByEmail, '/recover-password/<email>')
api.add_resource(ClienteByID,"/get-cliente/<int:id>")
api.add_resource(PetByID,"/get-pet/<int:id>")
api.add_resource(EspecialidadByID,"/get-especialidad/<int:id>")
JWTManager(app)