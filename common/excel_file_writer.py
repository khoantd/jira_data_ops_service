

from openpyxl import Workbook


def excel_file_write(filename, input_data):
    workbook = Workbook()
    worksheet = workbook.active
    # print(input_data)
    for i in range(len(input_data)):
        # print(input_data[i])
        worksheet.append(input_data[i])
    workbook.save(filename)


if __name__ == "__main__":
    print("excel_file_write")
