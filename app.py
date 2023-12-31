from flask import Flask, render_template, jsonify, redirect, request
from flask_restful import reqparse, abort, Api, Resource
from flask_cors import CORS
import mysql.connector
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import requests

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins":"*"}})
api = Api(app)

db = mysql.connector.connect(
    host = "localhost",
    user = "root",
    password = "",
    database = "gotit_db",
    port = "3306"
)

cursor = db.cursor()
parser = reqparse.RequestParser()
parser.add_argument("status")

class lostTable(Resource):
    def get(self):
        cursor.execute("SELECT * FROM lost_items")
        column = cursor.column_names
        data = cursor.fetchall()
        content = []
        subcontent = {}
        for datum in data:
            for x, y in zip(column, datum):
                if x == "image" and y != None:
                    y = "BLOB length " + str(len(y))
                subcontent[x] = y

            content.append(subcontent)
            subcontent = {}

        
        requested = {"table_name" : "lost_items", "table_content" : content}
        
        return jsonify(requested)

    def post(self):        
        query = parser.parse_args()
        print(query)
        if query['status'] != None:
            cursor.execute("SELECT * FROM lost_items WHERE status = " + "'" + str(query['status']) + "'")

            column = cursor.column_names
            data = cursor.fetchall()
            content = []
            subcontent = {}
            for datum in data:
                for x, y in zip(column, datum):
                    if x == "image" and y != None:
                        y = "BLOB length " + str(len(y))
                    subcontent[x] = y
                content.append(subcontent)
                subcontent = {}

        requested = {"table_name" : "lost_items", "table_content" : content}
        
        return jsonify(requested)

class foundTable(Resource):
    def get(self):
        cursor.execute("SELECT * FROM found_items")
        column = cursor.column_names
        data = cursor.fetchall()
        content = []
        subcontent = {}
        for datum in data:
            for x, y in zip(column, datum):
                if x == "image" and y != None:
                    y = "BLOB length " + str(len(y))
                subcontent[x] = y
            content.append(subcontent)
            subcontent = {}

        requested = {"table_name" : "found_items", "table_content" : content}
        return jsonify(requested)

    def post(self):
        query = parser.parse_args()
        if query['status'] != None:
            cursor.execute("SELECT * FROM found_items WHERE status = " + "'" + str(query['status']) + "'")


            column = cursor.column_names
            data = cursor.fetchall()
            content = []
            subcontent = {}
            for datum in data:
                for x, y in zip(column, datum):
                    if x == "image" and y != None:
                        y = "BLOB length " + str(len(y))
                    subcontent[x] = y
                content.append(subcontent)
                subcontent = {}

            requested = {"table_name" : "found_items", "table_content" : content}
            return jsonify(requested)

class matchTable(Resource):
    def get(self):
        cursor.execute("SELECT * FROM matched_items")
        column = cursor.column_names
        data = cursor.fetchall()
        content = []
        subcontent = {}
        for datum in data:
            for x, y in zip(column, datum):
                subcontent[x] = y
            content.append(subcontent)
            subcontent = {}

        requested = {"table_name" : "matched_items", "table_content" : content}
        return jsonify(requested)

class startMatch(Resource):
    def get(self):
        lostUrl = "http://127.0.0.1:5000/api/lost"
        foundUrl = "http://127.0.0.1:5000/api/found"
        #headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'}
        headers = {"Content-Type": "application/json"}
        param = {'status' : 0}
        parser.add_argument('status', type=int)
        requestLostData = requests.post(lostUrl, json=param, headers=headers)
        requestFoundData = requests.post(foundUrl, json=param, headers=headers)

        lostData = requestLostData.json()
        foundData = requestFoundData.json()        
        content = []
        for ldatum in lostData['table_content']:
            for fdatum in foundData['table_content']:
                if ldatum['category'] == fdatum['category']:
                    if ldatum['color'] == fdatum['color'] or ldatum['color'] == "":
                        if ldatum['brand'] == fdatum['brand'] or ldatum['brand'] == "":
                            fuzzResult = fuzz.token_sort_ratio(ldatum['description'], fdatum['description'])
                            if fuzzResult >= 55:
                                subcontent = (ldatum['ID'], fdatum['ID'], 0)
                                content.append(subcontent)
                                cursor.execute("UPDATE lost_items SET status = 1 WHERE ID = " + str(ldatum['ID']))
                                cursor.execute("UPDATE found_items SET status = 1 WHERE ID = " + str(fdatum['ID']))
                                db.commit()

        for matchedItem in content:
            insertData = "INSERT INTO matched_items (lost_id, found_id, status) VALUES " + str(matchedItem)
            cursor.execute(insertData)
            db.commit()

        return jsonify({"status" : 200})


# lau wan jing: manage users feature
parser = reqparse.RequestParser()
parser.add_argument('user_id', type=int)
parser.add_argument('activate', type=bool)
parser.add_argument('deactivate', type=bool)

class manageUsers(Resource):
    def get(self):
        cursor.execute("SELECT * FROM users")
        column = cursor.column_names
        data = cursor.fetchall()
        content = []
        subcontent = {}
        for datum in data:
            for x, y in zip(column, datum):
                subcontent[x] = y
            content.append(subcontent)
            subcontent = {}

        requested = {"table_name": "users", "table_content": content}
        return jsonify(requested)

    def post(self):
        args = parser.parse_args()
        user_id = args['user_id']

        if args['activate']:
            status = 1
        elif args['deactivate']:
            status = 0
        else:
            # Handle invalid request (neither activate nor deactivate specified)
            abort(400, message='Invalid request. Please specify activate or deactivate.')

        try:
            cursor.execute("UPDATE users SET status = %s WHERE ID = %s", (status, user_id))
            db.commit()
            return {"status": "success"}
        except Exception as e:
            # Handle database errors
            db.rollback()
            abort(500, message=f"Error: {str(e)}")



api.add_resource(manageUsers, "/api/manageusers")
api.add_resource(lostTable, "/api/lost")
api.add_resource(foundTable, "/api/found")
api.add_resource(startMatch, "/api/startmatch")

if __name__ == '__main__':
   app.run(debug=True)
