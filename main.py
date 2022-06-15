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
    key = request.headers.get('email-server-key')
    if key == os.environ.get('EMAIL_SERVER_KEY'):
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
    else:
        return JSONResponse(status_code=401, content={"message": "Unauthorized"})


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
            await create_invoice_document(document_context, background_tasks)
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
