import csv


def generate_csv(column_list: list, file_name: str, data: list):
    """create csv file and write data to it"""
    csv_columns = column_list
    csv_file = file_name

    try:
        with open(csv_file, 'w', encoding='utf8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            for item in data:
                writer.writerow(item)
    except IOError:
        print('error')
