# Forgot what this script does, figure it out later...
paragraphs = []

def get_file_path_from_user():
    print("Specify the path location for the file you want to target:")
    path = input()
    return path.strip()


def read_file(file_path):
    file = open(file_path, "r")

    for line in file:
        if line == "\n":
            continue

        if line[0] == "[" or line[0] == "<":
            paragraphs.append(line.strip() + "\n")
            continue

        paragraphs.append("<p>\n\t" + line.strip() + "\n</p>\n")

    file.close()


def get_new_path():
    print("\nEnter the path and file name for the new file including its extension")
    new_path_name = input()
    return new_path_name.strip()


def create_new_file(new_path_name):
    new_file = open(new_path_name, "w")

    for paragraph in paragraphs:
        new_file.write(paragraph + "\n")

    new_file.close()


file_path = get_file_path_from_user()
read_file(file_path)
new_file_path = get_new_path()
create_new_file(new_file_path)