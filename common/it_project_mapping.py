def project_categorize(argument):
    operation_name = {
        'FIN': 'IT Development Center',
        'IIB': 'IT Development Center',
        'VIT Development CenterG': 'IT Development Center',
        'CMS': 'IT Development Center',
        'VYMO': 'IT Development Center',
        'IS': 'IT Development Center',
        'ICL': 'IT Development Center',
        'ED': 'IT Development Center',
        'PELU': 'IT Development Center',
        'PCR': 'IT Development Center',
        'OM': 'IT Development Center',
        'HF': 'IT Development Center',
        'GN': 'IT Development Center',
        'CFA': 'IT Development Center',
        'IN': 'IT Development Center',
        'IA': 'IT Development Center',
        'NDS': 'IT Development Center',
        'IBM': 'IT Development Center',
        'CL': 'IT Development Center',
        'RLKL': 'IT Development Center',
        'BCA': 'IT Development Center',
        'N23': 'IT Development Center',
        'SH3': 'IT Development Center',
        'CSM': 'IT Development Center'
    }
    return operation_name.get(argument, "Not Available")


if __name__ == "__main__":
    argument = "Request to PROD"
