from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps

app = Flask(__name__)

app.config['SECRET_KEY'] = 'thisissecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(50))
    password = db.Column(db.String(80))
    admin = db.Column(db.Boolean)

class Courses(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    complete = db.Column(db.Boolean)
    user_id = db.Column(db.Integer)

#db.create_all()

# def token_required(f):
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         token = None

#         if 'x-access-token' in request.headers:
#             token = request.headers['x-access-token']

#         if not token:
#             return jsonify({'message' : 'Token is missing!'}), 401

#         try: 
#             data = jwt.decode(token, app.config['SECRET_KEY'])
#             current_user = User.query.filter_by(public_id=data['public_id']).first()
#         except:
#             return jsonify({'message' : 'Token is invalid!'}), 401

#         return f(current_user, *args, **kwargs)

#     return decorated

@app.route('/user', methods=['GET'])
#@token_required
def get_all_users():#current_user

    #if not current_user.admin:
        #return jsonify({'message' : 'Cannot perform that function!'})

    users = User.query.all()

    output = []

    for user in users:
        user_data = {}
        user_data['public_id'] = user.public_id
        user_data['name'] = user.name
        user_data['password'] = user.password
        user_data['admin'] = user.admin
        output.append(user_data)

    return jsonify({'users' : output})

@app.route('/user/<public_id>', methods=['GET'])
#@token_required
def get_one_user(public_id):#, current_user, 

    # if not current_user.admin:
    #     return jsonify({'message' : 'Cannot perform that function!'})

    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'message' : 'No user found!'})

    user_data = {}
    user_data['public_id'] = user.public_id
    user_data['name'] = user.name
    user_data['password'] = user.password
    user_data['admin'] = user.admin

    return jsonify({'user' : user_data})

@app.route('/user', methods=['POST'])
#@token_required
def create_user():#current_user
    # if not current_user.admin: 
    #     return jsonify({'message' : 'Cannot perform that function!'})

    data = request.get_json()

    hashed_password = generate_password_hash(data['password'], method='sha256')

    new_user = User(public_id=str(uuid.uuid4()), name=data['name'], password=hashed_password, admin=False)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message' : 'New user created!'})

@app.route('/user/<public_id>', methods=['PUT'])
#@token_required
def promote_user(public_id):#, current_user, 
    # if not current_user.admin:
    #     return jsonify({'message' : 'Cannot perform that function!'})

    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'message' : 'No user found!'})

    user.admin = True
    db.session.commit()

    return jsonify({'message' : 'The user has been promoted!'})

@app.route('/user/<public_id>', methods=['DELETE'])
#@token_required
def delete_user(public_id):# current_user, 
    # if not current_user.admin:
    #     return jsonify({'message' : 'Cannot perform that function!'})

    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'message' : 'No user found!'})

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message' : 'The user has been deleted!'})


# Endpoint for login
@app.route('/login')
def login():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})

    user = User.query.filter_by(name=auth.username).first()

    if not user:
        return make_response('Could not verify', 404, {'WWW-Authenticate' : 'Basic realm="User doesnt exist!"'})

    if check_password_hash(user.password, auth.password):
        token = jwt.encode({'public_id' : user.public_id, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])

        return jsonify({'token' : token})

    return make_response('Could not verify', 401, {'WWW-Authenticate' : 'Basic realm="Incorrect password!"'})


#Endpoint for listing courses
@app.route('/courses', methods=['GET'])
#@token_required
def get_all_courses():#current_user
    coursesl = Courses.query.all()

    output = []

    for courses in coursesl:
        courses_data = {}
        courses_data['id'] = courses.id
        courses_data['title'] = courses.title
        courses_data['description'] = courses.description
        courses_data['complete'] = courses.complete
        output.append(courses_data)

    return jsonify({'coursesl' : output})


#Endpoint for displaying course
@app.route('/courses/<courses_id>', methods=['GET'])
#@token_required
def get_one_courses(courses_id):#current_user, 
    courses = Courses.query.filter_by(id=courses_id).first()#, user_id=current_user.id

    if not courses:
        return jsonify({'message' : 'No courses found!'})

    courses_data = {}
    courses_data['id'] = courses.id
    courses_data['description'] = courses.description
    courses_data['title'] = courses.title
    courses_data['complete'] = courses.complete

    return jsonify(courses_data)


#Endpoint for adding course
@app.route('/courses', methods=['POST'])
#@token_required
def create_courses():#current_user
    data = request.get_json()

    if not data or 'title' not in data:
        return jsonify({'message': 'Missing required data'}), 400
    
    new_courses = Courses(title=data['title'], description=data.get('description', ''))# , user_id=current_user.id
    db.session.add(new_courses)
    db.session.commit()

    return jsonify({'message': "Course created!"}), 201

@app.route('/courses/<courses_id>', methods=['PUT'])
#@token_required
def complete_courses(courses_id):#current_user, 
    courses = Courses.query.filter_by(id=courses_id).first()#, , user_id=current_user.id

    if not courses:
        return jsonify({'message' : 'No courses found!'})

    courses.complete = True
    db.session.commit()

    return jsonify({'message' : 'courses item has been completed!'})

@app.route('/courses/<courses_id>', methods=['DELETE'])
#@token_required
def delete_courses(courses_id):#,current_user, 
    courses = Courses.query.filter_by(id=courses_id).first()#, , user_id=current_user.id

    if not courses:
        return jsonify({'message' : 'No courses found!'})

    db.session.delete(courses)
    db.session.commit()

    return jsonify({'message' : 'courses item deleted!'})

if __name__ == '__main__':
    app.run(debug=True)