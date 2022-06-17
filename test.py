import os


def get_all_email_templates_names(path):
    file_list = os.listdir(path)
    file_list = [file for file in file_list if not file.startswith('.')]
    print(file_list)


get_all_email_templates_names('./email_templates')
