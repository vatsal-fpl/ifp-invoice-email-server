import copy
import datetime


def custom_date_format(datestring):
    myDate = int(datetime.datetime.strptime(
        datestring, '%Y-%m-%d').strftime('%d'))
    month = datetime.datetime.strptime(datestring, '%Y-%m-%d').strftime('%b')
    year = datetime.datetime.strptime(datestring, '%Y-%m-%d').strftime('%Y')
    date_suffix = ["th", "st", "nd", "rd"]

    if myDate % 10 in [1, 2, 3] and myDate not in [11, 12, 13]:
        return f"{myDate}{date_suffix[myDate % 10]} {month} {year}"
    else:
        return f"{myDate}{date_suffix[0]} {month} {year}"


def get_invoice_context(document_dict):
    context = copy.deepcopy(document_dict)
    context['startDate'] = custom_date_format(context['startDate'])
    context['endDate'] = custom_date_format(context['endDate'])
    context["createdAt"] = context["startDate"]
    context["plan"] = context["plan"].upper()
    if context["send_email_flag"] is None:
        context["send_email_flag"] = False
    return context
