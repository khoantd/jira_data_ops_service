def project_type_categorize(argument):
    operation_name = {
        'True': 'Team-managed software',
        'False': 'Company-managed software',
    }
    return operation_name.get(argument, "Not Available")


if __name__ == "__main__":
    argument = "Request to PROD"
