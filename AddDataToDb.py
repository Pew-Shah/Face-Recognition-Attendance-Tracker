import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("serviceAccountKey.json")

firebase_admin.initialize_app(cred,{
    'databaseURL': "https://adr-reporting-a3c17-default-rtdb.firebaseio.com/"
})

ref = db.reference('Students')

data = {
    "321654":
        {
            "name": "Abc Efg",
            "id" : 321654,
            "standing": 4,
            "major": "Robotics",
            "starting_year": 2017,
            "total_attendance": 5,
            "year":4,
            "last_attendance_time":"2022-12-11 00:54:34"
        },
"898999":
        {
            "name": "Piyush Shah",
            "id": 898999,
            "standing": 4,
            "major": "CS",
            "starting_year": 2021,
            "total_attendance": 9,
            "year":4,
            "last_attendance_time":"2022-01-11 00:25:30"
        }
}


for key,value in data.items():
    ref.child(key).set(value)