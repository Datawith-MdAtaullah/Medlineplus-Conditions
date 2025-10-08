# This is a practice file for testing code snippets.
# It does not perform any actual functionality.
# data = {}
# cond = ['nazish', 'atmmmm']
# id = 10
# for c in cond:
#     syn = [f"{c}_syn1", f"{c}_syn3"]   
#     filename = c
#     file_path = f'genes/conditions/{filename}.json'
    
#     data[filename] = file_path
#     data[id] = c
#     for s in syn:
#         syn_filename = s
#         data[syn_filename] = file_path
            


# print(data)# End of practice file.

data = {}
cond = ['nazish', 'atmmmm']
id = "enrollment"

for c in cond:
    syn = [f"{c}_syn1", f"{c}_syn3"]
    filename = c
    file_path = f'genes/conditions/{filename}.json'
    
    if filename in data:
        print(f"⚠️ Key '{filename}' already exists, overwriting...")
    data[filename] = file_path

    if id in data:
        print(f"⚠️ Key '{id}' already exists, overwriting...")
    data[id] = c

    for s in syn:
        if s in data:
            print(f"⚠️ Key '{s}' already exists, overwriting...")
        data[s] = file_path

print(data)
