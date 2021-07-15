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
        if query['status'] != None:
            cursor.execute("SELECT * FROM lost_items WHERE status = " + "'" + query['status'] + "'")

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
            cursor.execute("SELECT * FROM found_items WHERE status = " + "'" + query['status'] + "'")


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
        param = {'status' : 0}
        requestLostData = requests.post(lostUrl, data=param)
        requestFoundData = requests.post(foundUrl, data=param)

        lostData = requestLostData.json()
        foundData = requestFoundData.json()
        print(foundData)
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




api.add_resource(lostTable, "/api/lost")
api.add_resource(foundTable, "/api/found")
api.add_resource(startMatch, "/api/startmatch")

if __name__ == '__main__':
   app.run(debug=True)
