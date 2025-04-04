import json

# List of file paths
file_paths = [
    '/home/peter/Desktop/Parsers/auto_sale/car_scraper/sprint_data_trucks.json',
    '/home/peter/Desktop/Parsers/auto_sale/car_scraper/sprint_data_motorbikes.json',
    '/home/peter/Desktop/Parsers/auto_sale/car_scraper/sprint_data_cars.json',
    '/home/peter/Desktop/Parsers/auto_sale/car_scraper/sprint_data_buses.json'
]

# Function to count the length of lists in JSON files


def count_list_length(file_paths):
    lengths = {}
    for path in file_paths:
        with open(path, 'r') as file:
            data = json.load(file)
            lengths[path] = len(data)
    return lengths


# Get the lengths
list_lengths = count_list_length(file_paths)
print(list_lengths)
