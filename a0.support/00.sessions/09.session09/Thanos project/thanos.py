import random
import os

folder_path = input("Thanos project/universe")

files = os.listdir(folder_path)

num_files_to_delete = len(files) // 2

random_files = random.sample(files, num_files_to_delete)

for file in random_files:
    os.remove(os.path.join(folder_path, file))

print("I Am Inevitable")