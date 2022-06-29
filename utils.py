from dotenv import load_dotenv
from cgitb import html
import mimetypes
import os
import platform
from re import template
from typing import IO
from wsgiref import headers
from fastapi import BackgroundTasks, UploadFile
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import datetime
import subprocess
import time
from db import get_collection
from bson.objectid import ObjectId
from docxtpl import DocxTemplate
from logger import get_logger

load_dotenv('./.env')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


logger1 = get_logger('general_logs', 'general_logs.log')
logger2 = get_logger('email_logs', 'email_logs.log')

if platform.system() == "Windows":
    libreoffice_path = os.environ.get(
        'LIBREOFFICE_PATH', 'C:\\Program Files\\LibreOffice\\program\\soffice.exe')
    ISWINDOWS = True
else:
    print("Not windows")
    libreoffice_path = '/usr/bin/soffice'
    ISWINDOWS = False
# ----------------------------------------------------------------
conf = ConnectionConfig(
    MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
    MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
    MAIL_FROM="no-reply@ilaforplacements.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_TLS=True,
    MAIL_SSL=False,
    TEMPLATE_FOLDER="./email_templates",
    MAIL_FROM_NAME="ILA for Placements"
)
# ----------------------------------------------------------------


async def send_email_async(subject, email_to, template_body=None, body=None, template_name=None):
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        title="ILA for Placements",
        body=body,
        subtype='html',
    )
    if template_body is not None:
        message.template_body = template_body

    if template_name is not None:
        template_name = template_name+".html"

    fm = FastMail(conf)
    await fm.send_message(message, template_name=template_name)
# ----------------------------------------------------------------


async def send_email_background(background_tasks: BackgroundTasks, subject, email_to, template_body=None, body=None, template_name=None):
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        title="ILA for Placements",
        body=body,
    )
    if template_body is not None:
        message.template_body = template_body

    if template_name is not None:
        template_name = template_name+".html"
        message.subtype = 'html'

    fm = FastMail(conf)

    background_tasks.add_task(fm.send_message, message,
                              template_name=template_name)
    logger2.info(f"Sent email to {email_to}")

# ----------------------------------------------------------------


async def send_mail_with_attachment_background(subject, email_to, path, background_tasks: BackgroundTasks, template_name=None, template_body=None, body=None):
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        title="ILA for Placements",
        attachments=[
            {
                "file": path,
                "filename": "attachment",
            }
        ]
    )
    if template_body is not None:
        message.template_body = template_body

    if template_name is not None:
        template_name = template_name+".html"
        message.subtype = 'html'

    if body is not None:
        message.body = body
    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message,
                              template_name=template_name)


# ----------------------------------------------------------------


def delete_file(path):
    try:
        os.remove(path)
        logger1.info(f"file deleted from path {path}")
        print("file deleted")
    except Exception as e:
        logger1.info(e)
        print(e)
# ----------------------------------------------------------------


async def get_username(user_id):
    try:
        database = 'ifp-b2c-prod'
        student_collection = get_collection(database, "student")
        student_data = student_collection.find_one(
            {"userId": ObjectId(user_id)})
        first_name = str(student_data.get('firstName'))
        last_name = str(student_data.get('lastName'))
        user_name = first_name+" "+last_name
        return user_name
    except:
        user_name = "User"
        return user_name
# ----------------------------------------------------------------


def calculate_cv_score(user_id):
    net_score = 0
    student = get_collection(
        "ifp-b2c-prod", "student").find_one({"userId": ObjectId(user_id)})
    if(student is not None):
        education = len([{"_id": str(education.get("_id"))} for education in get_collection(
            'ifp-b2c-prod', 'education').find({"userId": ObjectId(user_id)})])

        work_experience = len([{"_id": str(work_experience.get("_id"))} for work_experience in get_collection(
            'ifp-b2c-prod', 'workExperience').find({"userId": ObjectId(user_id)})])

        project = len([{"_id": str(project.get("_id"))} for project in get_collection(
            'ifp-b2c-prod', 'project').find({"userId": ObjectId(user_id)})])

        skill = len([{"_id": str(skill.get("_id"))} for skill in get_collection(
            'ifp-b2c-prod', 'skill').find({"userId": ObjectId(user_id)})])

        award = len([{"_id": str(award.get("_id"))} for award in get_collection(
            'ifp-b2c-prod', 'award').find({"userId": ObjectId(user_id)})])

        certification = len([{"_id": str(certification.get("_id"))} for certification in get_collection(
            'ifp-b2c-prod', 'certification').find({"userId": ObjectId(user_id)})])
        net_score += min(education*10, 30)
        net_score += min(work_experience*10, 20)
        net_score += min(project*10, 20)
        net_score += min(skill*5, 10)
        net_score += min(award*5, 10)
        net_score += min(certification*5, 10)
        return net_score
    else:
        return net_score
# -------------------------------------------------------------------------------------------------------


def get_cash_users():
    """get all users who have paid through cash"""
    subscriptions = get_collection('ifp-b2c-prod', 'subscription').find({
        'paymentType': 'cash'
    })
    cash_users = [str(subscription.get('userId'))
                  for subscription in subscriptions]

    print(cash_users)
    return cash_users

# ------------------------------------------------------------------------------------------------


def get_razorpay_users():
    """get all users who have paid through razorpay"""
    subscriptions = get_collection('ifp-b2c-prod', 'subscription').find({
        'paymentType': 'razorpay'
    })
    cash_users = [str(subscription.get('userId'))
                  for subscription in subscriptions]

    print(cash_users)
    return cash_users

# ------------------------------------------------------------------------------------------------


async def get_all_users(database):
    """get all users"""
    users_collection = get_collection(database, 'users').find({})
    all_users = [str(user.get('_id'))
                 for user in users_collection]

    return all_users

# ----------------------------------------------------------------------------------------


async def get_paid_users(database, collection):
    subscriptions = get_collection(database, collection).find({})
    paid_users = [str(subscription.get('userId'))
                  for subscription in subscriptions]
    print(paid_users)
    return paid_users


# ----------------------------------------------------------------------------------------
def get_user_email(user_id):
    user = get_collection(
        'ifp-b2c-prod', 'users').find_one({'_id': ObjectId(user_id)})
    if user is not None:
        return user.get('email')
    return None


# ------------------------------------------------------------------------------------------------


def check_login(user_id):
    """check if user is logged in once or not"""
    query = {"userId": ObjectId(user_id), "firstName": {
        "$exists": False}, "lastName": {"$exists": False}}
    user = get_collection('ifp-b2c-prod', 'student').find_one(query)
    if user is None:
        return True
    return False

# -----------------------------------------------------------------------------------------------


async def check_subscription_free(endDate, n_days, user_email, user_name, background_tasks: BackgroundTasks):
    date_now = datetime.datetime.now().date()
    endDate = datetime.datetime.fromtimestamp(endDate/1000).date()
    if endDate < date_now:
        await send_email_background(
            subject="Subscription expired",
            email_to=user_email,
            template_name="freeTrialExpired",
            template_body={"name": user_name},
            background_tasks=background_tasks
        )
        print("Subscription expired")
        logger2.info(f"{'freeTrialExpired'}:{user_email}")
    for n_day in n_days:
        timedelta = datetime.timedelta(days=n_day)
        if (endDate-timedelta) == date_now:
            nextDate = endDate + datetime.timedelta(days=1)
            await send_email_background(
                background_tasks=background_tasks,
                subject="Subscription will expire in {} days".format(
                    str(n_day)),
                email_to=user_email,
                template_body={"name": user_name, "daysLeft": str(
                    n_day), "endDate": str(endDate), "nextDate": str(nextDate)},
                template_name="freeTrialEndingInNdays",
            )
            logger2.info(f"{'freeTrialEndingInNdays'}:{user_email}")
            print("Subscription about to expire")
    if (endDate - timedelta) > date_now:
        print(f"Subscription is valid for {user_email}")

# ------------------------------------------------------------------------------------------------------------


async def check_subscription_paid(endDate, n_days, user_email, user_plan, user_name, background_tasks: BackgroundTasks):
    print("inside the check subscription paid ------------------------------")
    date_now = datetime.datetime.now().date()
    endDate = datetime.datetime.strptime("2022-06-27", "%Y-%m-%d").date()
    print(endDate, "-----------------", user_email)
    template_body = {
        "name": user_name,
    }
    if endDate < date_now:
        print("Subscription expired")
        # change template for subscription expired
        template_name = "subscriptionExpiredPaid"
        # await send_email_background(
        #     background_tasks=background_tasks,
        #     subject="Oops! Your subscription has expired…",
        #     email_to=user_email,
        #     template_name=template_name,
        #     template_body=template_body,
        # )
    for n_day in n_days:
        print(f"Checking subscription for {n_day} days")
        timedelta = datetime.timedelta(days=n_day)
        if (endDate-timedelta) == date_now:
            nextDate = endDate + datetime.timedelta(days=1)
            if n_day == 1:
                print("Subscription will expire in one day")
                template_name = "oneDayRemainingPaid"
                subject = "Your ILA for Placements subscription is almost over!"
            if n_day == 5:
                print("Subscription will expire in one day")
                if user_plan == "basic":
                    template_name = "fiveDaysRemainingBasic"
                    subject = "Upgrade Your Plan Now!"
                elif user_plan == "essential":
                    template_name = "fiveDaysRemainingEssential"
                    subject = " Upgrade Your Plan Now!"
                else:
                    template_name = "subscriptionExpiredPaid"
                    subject = "Oops! Your subscription has expired…"
            if n_day == 7:
                print("Subscription will expire in one day")
                template_name = "sevenDaysRemainingPaid"
                template_body = {"name": user_name, "daysLeft": str(n_day), "endDate": str(
                    endDate), "nextDate": str(nextDate), "plan": user_plan}

            # await send_email_background(
            #     subject=subject,
            #     email_to=user_email,
            #     template_name=template_name,
            #     template_body=template_body,
            #     background_tasks=background_tasks
            # )

    if (endDate - timedelta) > date_now:
        print(f"Subscription is valid for {user_email}")

# ------------------------------------------------------------------------------------------------------------


async def create_invoice_document(document_context, background_tasks: BackgroundTasks):
    invoice_template_path = BASE_DIR+"/invoice_template/invoice.docx"
    doc = DocxTemplate(invoice_template_path)
    doc.render(document_context)
    invoice_id = document_context.get("invoiceNumber")
    folder_name = invoice_id.split("/")[0]
    invoice_no = "Invoice_" + invoice_id.split("/")[1]
    invoice_path = BASE_DIR+"/invoices/"+folder_name
    if not os.path.exists(invoice_path):
        os.makedirs(invoice_path)
    docx_path = BASE_DIR + f"/generated_documents/"+str(invoice_no)+".docx"
    doc.save(docx_path)
    # subprocess.check_output([libreoffice_path, '--headless', '--invisible', '--convert-to',
    #                         'pdf', f"generated_documents/{invoice_no}.docx", '--outdir', f"invoices/{folder_name}/"])
    try:
        subprocess.run(
            ["doc2pdf", docx_path])
        subprocess.run(
            ["mv", f"generated_documents/"+f"{invoice_no}"+'.pdf', f"{BASE_DIR}/invoices/{folder_name}/"])
    except:
        print('Error converting docx to pdf!')

    userId = document_context.get("userId")
    user_name = get_username(userId)
    send_email_flag = document_context.get("send_email_flag")
    pdf_path = BASE_DIR + f"/invoices/{folder_name}/{invoice_no}"+".pdf"

    if send_email_flag == False:
        background_tasks.add_task(delete_file, docx_path)
    else:
        await send_mail_with_attachment_background(
            subject="Congratulations!V Your payment is successful",
            email_to=document_context.get("billEmail"),
            path=pdf_path,
            template_name="newSubscriptionActived",
            template_body={
                "name": user_name,
            },
            background_tasks=background_tasks
        )
        user_email = document_context.get("billEmail")
        logger2.info(f"{'newSubscriptionActived'}:{user_email}")
        background_tasks.add_task(delete_file, docx_path)


# ------------------------------------------------------------------------------------------------------------
async def create_invoice_document2(document_context, background_tasks: BackgroundTasks):
    print("Inside the create_invoice_document2")
    invoice_template_path = BASE_DIR+"/invoice_template/invoice.docx"
    doc = DocxTemplate(invoice_template_path)
    doc.render(document_context)
    invoice_path = BASE_DIR+"/invoices/"
    invoice_no = document_context.get("paymentId")
    print(invoice_no, "---------------invoice no")
    if not os.path.exists(invoice_path):
        os.makedirs(invoice_path)
    docx_path = BASE_DIR + f"/generated_documents/"+str(invoice_no)+".docx"
    doc.save(docx_path)
    subprocess.check_output([libreoffice_path, '--headless', '--invisible', '--convert-to',
                            'pdf', f"generated_documents/{invoice_no}.docx", '--outdir', f"{BASE_DIR}/invoices/"])
    # try:
    #     subprocess.run(
    #         ["doc2pdf", docx_path])
    #     subprocess.run(
    #         ["mv", f"generated_documents/"+f"{invoice_no}"+'.pdf', f"{BASE_DIR}/invoices/"])
    # except:
    #     print('Error converting docx to pdf!')

    userId = document_context.get("userId")
    user_name = await get_username(userId)
    send_email_flag = document_context.get("send_email_flag")
    pdf_path = f"{BASE_DIR}/invoices/{invoice_no}"+".pdf"

    if send_email_flag == False:
        background_tasks.add_task(delete_file, docx_path)
    else:

        await send_mail_with_attachment_background(
            subject="Congratulations! Your payment is successful",
            email_to=document_context.get("billEmail"),
            path=pdf_path,
            template_name="newSubscriptionActived",
            template_body={
                "name": user_name,
            },
            background_tasks=background_tasks
        )
        user_email = document_context.get("billEmail")
        logger2.info(f"{'newSubscriptionActived'}:{user_email}")
        background_tasks.add_task(delete_file, docx_path)


# ---------------------- Check Subscription Status for free users


async def check_subscription_send_email_free(background_tasks: BackgroundTasks):
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
    for student in all_students:
        for user in free_users:
            if str(user.get("_id")) == str(student.get("userId")):
                user["firstName"] = student.get("firstName")
                user["lastName"] = student.get("lastName")

    for user in free_users:
        user_email = user.get("email")
        end_date = user.get("endDate")
        user_name = user.get("firstName") if user.get(
            "firstName") else "User"
        await check_subscription_free(endDate=end_date, n_days=[3], user_email=user_email, user_name=user_name, background_tasks=background_tasks)
# ---------------- Check Subscription Status for paid users------------------------


async def check_subscription_send_email_paid(background_tasks: BackgroundTasks):
    database = 'ifp-b2c-prod'
    subscritpion_collection = get_collection(database, "subscription")
    users_collection = get_collection(database, "users")
    student_collection = get_collection(database, "student")
    all_students = student_collection.find()
    all_users = users_collection.find()
    all_subscription = subscritpion_collection.find()
    subscriptions = [{
        "userId": str(subscription.get("userId")),
        "endDate": subscription.get("endDate"),
        "plan": subscription.get("plan"),
    } for subscription in all_subscription]

    for student in all_students:
        for subscription in subscriptions:
            if str(subscription.get("userId")) == str(student.get("userId")):
                subscription["firstName"] = student.get("firstName")
    for user in all_users:
        user_email = user.get("email")
        print(user_email)
        userId = user.get("_id")
        user_plan = user.get("plan")
        user_subscription = [subscription for subscription in subscriptions if subscription.get(
            "userId") == str(userId)]
        print("---------------- 1")
        if len(user_subscription) > 0:
            user_name = user_subscription[0].get(
                "firstName") if user_subscription[0].get("firstName") else "User"
            endDate = user_subscription[0].get("endDate")
            await check_subscription_paid(endDate, [1, 5, 7], user_email=user_email, user_plan=user_plan, user_name=user_name, background_tasks=background_tasks)


# ---------------------- get all email templates list ----------------------
def get_all_email_templates_names(path):
    file_list = os.listdir(path)
    file_list = [file for file in file_list if not file.startswith('.')]
    print(file_list)
# -----------------------------------------
