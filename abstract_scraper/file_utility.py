import csv, re, os, shutil

class FileUtility:
    @staticmethod
    def read_papers(path, entries, start_entry = 0):
        with open(path) as f:
            csv_reader = csv.reader(f)
            # Skip rows until the desired starting row
            for _ in range(start_entry):
                next(csv_reader, None)

            if entries == -1:
                return [row for row in csv_reader] 

            return [next(csv_reader) for _ in range(entries)]

    @staticmethod
    def make_dir(output):
        if os.path.exists(output):
            shutil.rmtree(output)
        os.makedirs(output)

class File:
    def __init__(self, path, header = []):
        self.path = path
        self.fd = open(path, 'a+')
        self.writer = csv.writer(self.fd)
        # self.writer.writerow(header)

    def add_row(self, row):
        self.writer.writerow(row)

    def close(self):
        self.fd.close()
