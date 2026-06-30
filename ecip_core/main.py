from ecip_core.storage.sqlite.repository import JavaRepository

repository = JavaRepository()

print("\nAll Files")
print(repository.get_all_files())

print("\nUserService")
print(repository.find_by_class_name("UserService"))

print("\nMethods")
print(repository.find_methods("UserService"))

print("\nMethod Search")
print(repository.find_file_by_method("getUser"))