import requests


def check_paid_users_subscription_cron():
    headers = {
        "email-server-key": "et74a%^O2qnq55gDDfCFfbim%4m#Lca"
    }
    url = 'http://127.0.0.1:8000/check_subscription_paid'
    result = requests.post(url=url, headers=headers)
    print("Task Completed")


if __name__ == '__main__':
    check_paid_users_subscription_cron()
