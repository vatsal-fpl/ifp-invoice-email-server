import email
from unittest import async_case
from utils import *
import json
from fastapi import FastAPI, BackgroundTasks, Request, File, UploadFile, Form, Query, Path, Body
from starlette.requests import Request
from starlette.responses import JSONResponse, FileResponse
from context.invoice_context import get_invoice_context
from dotenv import load_dotenv
import os
import platform
from fastapi.middleware.cors import CORSMiddleware
from utils import send_email_background, delete_file, create_invoice_document, check_subscription_send_email_free, check_subscription_send_email_paid
from logger import get_logger
from pydantic import BaseSettings
from models.invoice import Invoice
from cronjob import *

logger1 = get_logger('general_logs', 'general_logs.log')
logger2 = get_logger('email_logs', 'email_logs.log')


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Settings(BaseSettings):
    openapi_url: str = ""


settings = Settings()
load_dotenv('./.env')

WHITELISTED_IPS = json.loads(os.getenv('WHITELISTED_IPS'))
logger = get_logger("main")

origins = ["*"]
app = FastAPI(openapi_url=settings.openapi_url)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/')
async def root(request: Request):
    logger1.info("Request from: " + request.client.host)
    return {
        "message": "Welcome to FinePrint Email Server with FASTAPI",
        "status": 200,
        "data": {
            "ip": request.client.host,
            "operating_system": platform.system(),
            "domain": request.url._url
        }
    }


@app.post("/send_email")
async def send_email(request: Request, background_tasks: BackgroundTasks):
    logger1.info("Requested the /send_email endpoint")
    key = request.headers.get('email-server-key')
    if key == os.environ.get('EMAIL_SERVER_KEY'):
        data = await request.json()
        logger1.info("sending email in background")
        await send_email_background(
            background_tasks=background_tasks,
            body=data.get('body'),
            email_to=data.get('email_to'),
            subject=data.get('subject'),
            template_body=data.get('template_body'),
            template_name=data.get('template_name'),
        )
        return JSONResponse(status_code=200, content={"message": "Email sent"})
    else:
        logger1.info("Key is invalid")
        return JSONResponse(status_code=401, content={"message": "Unauthorized"})


@app.post("/send_mail_with_attachment")
async def send_mail_with_attachment(request: Request, background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    logger1.info("Requested /send_mail_with_attachment endpoint")
    key = request.headers.get('email-server-key')
    if key == os.environ.get('EMAIL_SERVER_KEY'):
        logger1.info("Key is valid")
        try:
            logger1.info("Saving file in uploads")
            with open(os.path.join('uploads/', file.filename), 'wb') as f:
                f.write(file.file.read())
        except Exception as e:
            logger1.info(e)
            print(e)

        file_path = os.path.join('uploads/', file.filename)
        data = dict(await request.form())
        logger1.info("Sending email with attachment")
        await send_mail_with_attachment_background(
            background_tasks=background_tasks,
            body=data.get('body'),
            email_to=data.get('email_to'),
            path=file_path,
            subject=data.get('subject'),
            template_body=json.loads(data.get('template_body')),
            template_name=data.get('template_name'),
        )
        return JSONResponse(status_code=200, content={"message": "Email sent"})
    else:
        logger1.info("Key is invalid")
        return JSONResponse(status_code=401, content={"message": "Unauthorized"})


@app.get("/fetch_invoice")
async def fetch_invoice(request: Request, background_tasks: BackgroundTasks):
    logger1.info("Requested /fetch_invoice endpoint")
    try:
        logger1.info("fetching the invoice")
        query = request.query_params
        invoice_no = query.get('invoiceNumber')
        path = BASE_DIR + f"/invoices/{invoice_no}"+".pdf"
        if os.path.exists(path):
            background_tasks.add_task(delete_file, path)
            return FileResponse(path, media_type="application/pdf", filename=f"{invoice_no}.pdf")
        else:
            logger1.info(f"Invoice not found with {invoice_no}")
            return JSONResponse(status_code=404, content={"message": "Invoice not found"})
    except Exception as e:
        logger1.info(e)
        return JSONResponse(status_code=500, content={"message": "Internal Server Error"})


@app.post('/create_send_invoice_with_docx')
async def create_send_invoice_with_docx(invoice: Invoice, request: Request, background_tasks: BackgroundTasks) -> JSONResponse:
    logger1.info("Requested /create_send_invoice_with_docx endpoint")
    key = request.headers.get('email-server-key')
    if key == os.environ.get('EMAIL_SERVER_KEY'):
        try:
            invoice_dict = invoice.dict()
            document_context = get_invoice_context(invoice_dict)
            await create_invoice_document2(document_context, background_tasks)
            return JSONResponse(status_code=200, content={"success": True, "message": "invoice has been created"})
        except Exception as e:
            logger1.info(e)
            print(e)
    else:
        return JSONResponse(status_code=403, content={'message': 'Oops! You are not allowed to access this server.'})


@app.post('/check_subscription_free')
async def check_subscription_free(request: Request, background_tasks: BackgroundTasks) -> JSONResponse:
    logger1.info("Requested /check_subscription_free endpoint")
    key = request.headers.get('email-server-key')
    if key == os.environ.get('EMAIL_SERVER_KEY'):
        try:
            await check_subscription_send_email_free(background_tasks=background_tasks)
            return JSONResponse(status_code=200, content={"success": True, "message": "subscription has been checked"})
        except Exception as e:
            print(e)
            logger1.info(e)
            return JSONResponse(status_code=500, content={"success": False, "message": "Internal Server Error"})
    else:
        return JSONResponse(status_code=403, content={'message': 'Oops! You are not allowed to access this server.'})


@app.post('/check_subscription_paid')
async def check_subscription_paid(request: Request, background_tasks: BackgroundTasks) -> JSONResponse:
    logger1.info("Requested /check_subscription_paid endpoint")
    key = request.headers.get('email-server-key')
    if key == os.environ.get('EMAIL_SERVER_KEY'):
        try:
            await check_subscription_send_email_paid(background_tasks=background_tasks)
            return JSONResponse(status_code=200, content={"success": True, "message": "subscription has been checked"})
        except Exception as e:
            print(e)
            logger1.info(e)
            return JSONResponse(status_code=500, content={"success": False, "message": "Internal Server Error"})
    else:
        return JSONResponse(status_code=403, content={'message': 'Oops! You are not allowed to access this server.'})


@app.post('/send_invite_email')
async def send_invite_email(request: Request, background_tasks: BackgroundTasks) -> JSONResponse:
    logger1.info("Requested /send_invite_email endpoint")
    key = request.headers.get('email-server-key')
    if key == os.environ.get('EMAIL_SERVER_KEY'):
        try:
            data = await request.json()
            email_list = data.get("email_list")
            template_name = data.get("template_name")
            subject = data.get("subject")

            def status(email):
                print("Task Done", email)

            for email in email_list:
                await send_email_background(
                    subject=subject,
                    email_to=email,
                    template_name=template_name,
                    template_body={"name": "", "email": email},
                    background_tasks=background_tasks
                )
                background_tasks.add_task(status, email)

            return JSONResponse(status_code=200, content={"success": True, "message": "email has been sent in background"})
        except Exception as e:
            logger1.info(e)
            return JSONResponse(status_code=500, content={"success": False, "message": "Internal Server Error"})
    else:
        return JSONResponse(status_code=403, content={'message': 'Oops! You are not allowed to access this server.'})


# change name of function (first type of users)
@app.post('/check_login_status_send_email')
async def check_login_status_send_email(request: Request, background_tasks: BackgroundTasks) -> JSONResponse:
    logger1.info("Requested /check_login_status_send_email endpoint")
    paid_users = await get_paid_users(
        database='ifp-b2c-prod', collection='subscription')
    data = []
    for user in paid_users:
        status = check_login(user)
        if status == False:
            email = get_user_email(user)
            await send_email_background(
                background_tasks=background_tasks,
                body="",
                email_to=email,
                subject="You havent logged in yet",
                template_body={"name": "User"},
                template_name="askForLogin"
            )
            logger2.info(f"{'askForLogin'}:{email} ")
    return JSONResponse(status_code=200, content={"success": True, "message": data})


@app.post('/check_cv_score_send_email')
async def check_cv_score_send_email(request: Request, background_tasks: BackgroundTasks) -> JSONResponse:
    logger1.info("Requested /check_cv_score_send_email endpoint")
    all_users = await get_all_users('ifp-b2c-prod')
    try:
        async def check_cv_score_send_email(all_users):
            for user in all_users:
                email = await get_user_email(user)
                name = await get_username(user)
                cv_score = calculate_cv_score(user)
                if cv_score >= 0 or cv_score <= 40:
                    await send_email_background(
                        background_tasks=background_tasks,
                        body="",
                        email_to=email,
                        subject="Your CV score is low",
                        template_body={"name": name},
                        template_name="cvScore0to40"
                    )
                    logger2.info(f"{'cvScore0to40'}:{email}")
                    print(email, cv_score, "greater than 0 or less than 40")
                elif cv_score >= 41 and cv_score < 70:
                    await send_email_background(
                        background_tasks=background_tasks,
                        body="",
                        email_to=email,
                        subject="Your CV score is low",
                        template_body={"name": name},
                        template_name="cvScore40to70"
                    )
                    logger2.info(f"{'cvScore40to70'}:{email}")
                    print(email, cv_score, "greater than 41 and less than 70")
                elif cv_score >= 70:
                    await send_email_background(
                        background_tasks=background_tasks,
                        body="",
                        email_to=email,
                        subject="Your CV score is low",
                        template_body={"name": name},
                        template_name="cvScore70above"
                    )
                    logger2.info(f"{'cvScore70above'}:{email}")
                    print(email, cv_score, "greater than 70")
        background_tasks.add_task(check_cv_score_send_email, all_users)
    except Exception as e:
        print(e)

    return JSONResponse(status_code=200, content={"success": True, "message": all_users})


@app.post('/test')
async def test(request: Request, background_tasks: BackgroundTasks) -> JSONResponse:
    await send_email_background(
        subject="Subscription expired",
        email_to="vatsal@fineprint.legal",
        template_name="freeTrialEndingInNdays",
        template_body={"name": "Vatsal", "daysLeft": "5",
                       "endDate": "2020-01-01", "nextDate": "2020-01-06", "extra": "data"},
        background_tasks=background_tasks
    )
    return JSONResponse(status_code=200, content={"success": True, "message": "email has been sent in background"})
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", port=8000, reload=True)
