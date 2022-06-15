from pydantic import BaseModel
from typing import Optional


class Invoice(BaseModel):
    userId: Optional[str]
    paymentId: Optional[str]
    billEmail: Optional[str]
    billContact: Optional[str]
    orderAmount: Optional[str]
    invoiceNumber: Optional[str]
    plan: Optional[str]
    startDate: Optional[str]
    endDate: Optional[str]
    send_email_flag: Optional[bool]
