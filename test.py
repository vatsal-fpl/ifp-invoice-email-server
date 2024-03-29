def send_email_sendgrid():
    import os
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail

    message = Mail(
        from_email='vatsal@fineprint.legal',
        to_emails='vatsal@fineprint.legal',
        subject='ILA for Placements',
        html_content='<strong>and easy to do anywhere, even with Python</strong>')
    try:
        sg = SendGridAPIClient(
            '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')
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)


send_email_sendgrid()
