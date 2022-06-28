from db import *

subscriptions = get_collection("ifp-b2c-prod", "subscription").find({})
paid_users = [str(subscription.get('userId'))
              for subscription in subscriptions]
print(paid_users)
