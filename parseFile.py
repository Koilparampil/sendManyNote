from os import path


def get_bookingNums_from_file(filename):
    lines =[]
    with open(filename, "r", encoding="utf-8") as f:
        lines = [line.strip().splitlines() for line in f if line.strip()]
        lines = [line.split()[0] for sublist in lines for line in sublist]
    return lines

class DataException(Exception):
    pass

if __name__ == "__main__":
    filename = "listOfBookings.txt"
    data = get_bookingNums_from_file(filename)
    print(data)