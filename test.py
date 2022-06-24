# import os


# def get_all_email_templates_names(path):
#     file_list = os.listdir(path)
#     file_list = [file for file in file_list if not file.startswith('.')]
#     print(file_list)


# get_all_email_templates_names('./email_templates')
from db import get_collection
import datetime

database = 'ifp-b2c-prod'
subscritpion_collection = get_collection(database, "subscription")
users_collection = get_collection(database, "users")
all_subscription = subscritpion_collection.find()
all_users = users_collection.find()
paid_users = [subcription['userId']
              for subcription in all_subscription]
student_collection = get_collection(database, "student")
all_students = student_collection.find()
free_users = [{"_id": str(user.get('_id')),
               "email": str(user.get('email')),
               "endDate": int(datetime.datetime.strptime(user.get("createdDate"), '%Y-%m-%d').timestamp()) + (10*24*60*60)
               } for user in all_users if user['_id'] not in paid_users]

for user in free_users:
    print(user)
