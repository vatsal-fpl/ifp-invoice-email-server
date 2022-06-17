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
    logger.info("Request from: " + request.client.host)
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
    # key = request.headers.get('email-server-key')
    # if key == os.environ.get('EMAIL_SERVER_KEY'):
    data = await request.json()
    await send_email_background(
        background_tasks=background_tasks,
        body=data.get('body'),
        email_to=data.get('email_to'),
        subject=data.get('subject'),
        template_body=data.get('template_body'),
        template_name=data.get('template_name'),
    )
    return JSONResponse(status_code=200, content={"message": "Email sent"})
    # else:
    #     return JSONResponse(status_code=401, content={"message": "Unauthorized"})


@app.post("/send_mail_with_attachment")
async def send_mail_with_attachment(request: Request, background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    key = request.headers.get('email-server-key')
    if key == os.environ.get('EMAIL_SERVER_KEY'):
        try:
            with open(os.path.join('uploads/', file.filename), 'wb') as f:
                f.write(file.file.read())
        except Exception as e:
            print(e)

        file_path = os.path.join('uploads/', file.filename)
        data = dict(await request.form())

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
        return JSONResponse(status_code=401, content={"message": "Unauthorized"})


@app.get("/fetch_invoice")
async def fetch_invoice(request: Request, background_tasks: BackgroundTasks):
    try:
        query = request.query_params
        invoice_id = query.get('invoiceNumber')
        folder_name = invoice_id.split("/")[0]
        invoice_no = "Invoice_" + invoice_id.split("/")[1]
        print(invoice_no)
        path = BASE_DIR + f"/invoices/{folder_name}/{invoice_no}"+".pdf"
        print(path)
        if os.path.exists(path):
            background_tasks.add_task(delete_file, path)
            return FileResponse(path, media_type="application/pdf", filename=f"{invoice_no}.pdf")
        else:
            logger.error(f"Invoice not found for {invoice_id}")
            return JSONResponse(status_code=404, content={"message": "Invoice not found"})
    except Exception as e:
        logger.error(e)
        return JSONResponse(status_code=500, content={"message": "Internal Server Error"})


@app.post('/create_send_invoice_with_docx')
async def create_send_invoice_with_docx(invoice: Invoice, request: Request, background_tasks: BackgroundTasks) -> JSONResponse:
    key = request.headers.get('email-server-key')
    if key == os.environ.get('EMAIL_SERVER_KEY'):
        try:
            invoice_dict = invoice.dict()
            document_context = get_invoice_context(invoice_dict)
            await create_invoice_document2(document_context, background_tasks)
            return JSONResponse(status_code=200, content={"success": True, "message": "invoice has been created"})
        except Exception as e:
            logger.error(e)
    else:
        return JSONResponse(status_code=403, content={'message': 'Oops! You are not allowed to access this server.'})


@app.post('/check_subscription_free')
async def check_subscription_free(request: Request, background_tasks: BackgroundTasks) -> JSONResponse:
    key = request.headers.get('email-server-key')
    if key == os.environ.get('EMAIL_SERVER_KEY'):
        try:
            await check_subscription_send_email_free(background_tasks=background_tasks)
            return JSONResponse(status_code=200, content={"success": True, "message": "subscription has been checked"})
        except Exception as e:
            logger.error(e)
            return JSONResponse(status_code=500, content={"success": False, "message": "Internal Server Error"})
    else:
        return JSONResponse(status_code=403, content={'message': 'Oops! You are not allowed to access this server.'})


@app.post('/check_subscription_paid')
async def check_subscription_paid(request: Request, background_tasks: BackgroundTasks) -> JSONResponse:
    key = request.headers.get('email-server-key')
    if key == os.environ.get('EMAIL_SERVER_KEY'):
        try:
            await check_subscription_send_email_paid(background_tasks=background_tasks)
            return JSONResponse(status_code=200, content={"success": True, "message": "subscription has been checked"})
        except Exception as e:
            logger.error(e)
            return JSONResponse(status_code=500, content={"success": False, "message": "Internal Server Error"})
    else:
        return JSONResponse(status_code=403, content={'message': 'Oops! You are not allowed to access this server.'})


@app.post('/send_invite_email')
async def send_invite_email(request: Request, background_tasks: BackgroundTasks) -> JSONResponse:
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
            return JSONResponse(status_code=500, content={"success": False, "message": "Internal Server Error"})
    else:
        return JSONResponse(status_code=403, content={'message': 'Oops! You are not allowed to access this server.'})


# change name of function (first type of users)
@app.post('/check_login_status_send_email')
async def check_login_status_send_email(request: Request, background_tasks: BackgroundTasks) -> JSONResponse:
    paid_users = get_paid_users(
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
                template_body={"name": "User", "email": email},
                template_name="test"
            )
    return JSONResponse(status_code=200, content={"success": True, "message": data})


@app.post('/check_cv_score_send_email')
async def check_cv_score_send_email(request: Request, background_tasks: BackgroundTasks) -> JSONResponse:
    all_users = await get_all_users('ifp-b2c-prod')

    async def check_cv_score_send_email(all_users):
        for user in all_users:
            email = get_user_email(user)
            cv_score = calculate_cv_score(user)
            if cv_score >= 0 or cv_score <= 40:
                # await send_email_background(
                #     background_tasks=background_tasks,
                #     body="",
                #     email_to=email,
                #     subject="Your CV score is low",
                #     template_body={"name": "User", "email": email},
                #     template_name="test"
                # )
                print(email, cv_score, "greater than 0 or less than 40")
            elif cv_score >= 41 and cv_score < 70:
                # send email
                print(email, cv_score, "greater than 41 and less than 70")
            elif cv_score >= 70:
                # send email
                print(email, cv_score, "greater than 70")
    background_tasks.add_task(check_cv_score_send_email, all_users)

    return JSONResponse(status_code=200, content={"success": True, "message": all_users})


@app.post('/test')
async def test(request: Request, background_tasks: BackgroundTasks) -> JSONResponse:
    await send_email_background(
        subject="Subscription expired",
        email_to="vatsal@fineprint.legal",
        template_name="freeTrialEndingInNdays",
        template_body={"name": "Vatsal", "daysLeft": "5",
                       "endDate": "2020-01-01", "nextDate": "2020-01-06"},
        background_tasks=background_tasks
    )
    return JSONResponse(status_code=200, content={"success": True, "message": "email has been sent in background"})
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", port=8000, reload=True)
