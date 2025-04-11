
# # def get_full_name(first_name, last_name):
# #     full_name = first_name.title() + " " + last_name.title()
# #     return full_name


# # print(get_full_name("john", "doe"))
# def get_name_with_age(name: str, age: int):
#     name_with_age = name.title() + " is this old: " + str(age)
#     return name_with_age
# print(get_name_with_age("john", 34))
import os
anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
gpt_api_key = os.environ.get('GPT_API_KEY')

print(anthropic_api_key)
print(gpt_api_key)