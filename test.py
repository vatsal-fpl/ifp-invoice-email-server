import datetime

endDate = datetime.datetime.strptime("2022-06-27", "%Y-%m-%d").date()
date_now = datetime.datetime.now().date()
print(endDate < date_now)
