import ntpath


def guess_filename_stream(path_to_file):
    f = open(path_to_file, 'rb')
    buf = f.read()
    f.close()
    filename = ntpath.basename(path_to_file)
    return filename, buf


def read_file_as_string(file_path):
    with open(file_path, 'rb') as myfile:
        data = myfile.read()
    return data
