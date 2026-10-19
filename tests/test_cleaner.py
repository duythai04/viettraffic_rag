from src.preprocessing.cleaner import LegalTextCleaner


raw_text = """
Điều 7.    Xử phạt người điều khiển phương tiện


1.    Phạt tiền đối với hành vi vi phạm.


a)    Không chấp hành hiệu lệnh;



b)     Không tuân thủ quy định.
"""


cleaner = LegalTextCleaner()

cleaned_text = cleaner.clean(raw_text)


print("===== BEFORE =====")
print(raw_text)

print("===== AFTER =====")
print(cleaned_text)