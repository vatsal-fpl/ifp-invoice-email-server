import requests


def check_paid_users_subscription_cron():
    headers = {
        "email-server-key": "et74a%^O2qnq55gDDfCFfbim%4m#Lca"
    }
    url = 'https://emailserver.ilaforplacements.com/check_subscription_paid'
    result = requests.post(url=url, headers=headers)
    print("/check_paid_users_subscription_cron completed")


if __name__ == '__main__':
    check_paid_users_subscription_cron()
