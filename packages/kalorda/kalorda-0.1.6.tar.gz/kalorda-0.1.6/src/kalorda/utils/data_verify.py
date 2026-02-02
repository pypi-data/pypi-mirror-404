import re

from kalorda.utils.i18n import _


class DataVerify:
    result: bool
    message: str

    def __init__(self, result: bool = False, message: str = ""):
        self.result = result
        self.message = message


def is_valid_username(username: str) -> dict:
    """
    验证用户名格式是否正确
    """
    if not username:
        return DataVerify(result=False, message=_("用户名不能为空"))
    if len(username) < 2 or len(username) > 20:
        return DataVerify(result=False, message=_("用户名长度必须在2到20个字符之间"))
    if not re.search(r"^[a-zA-Z0-9\u4e00-\u9fa5]+$", username):
        return DataVerify(result=False, message=_("用户名只能只能中文或英文字母或数字"))
    return DataVerify(result=True, message=_("用户名格式正确"))


def is_valid_password(password: str) -> dict:
    """
    验证密码格式是否正确
    """
    if not password:
        return DataVerify(result=False, message=_("密码不能为空"))
    if len(password) < 6 or len(password) > 50:
        return DataVerify(result=False, message=_("密码长度必须在6到50个字符之间"))
    if password.isdigit():
        return DataVerify(result=False, message=_("密码不能是纯数字"))
    return DataVerify(result=True, message=_("密码格式正确"))


def is_valid_email(email: str) -> dict:
    """
    验证邮箱格式是否正确
    """
    if not email:
        return DataVerify(result=False, message=_("邮箱不能为空"))
    if len(email) < 6 or len(email) > 50:
        return DataVerify(result=False, message=_("邮箱长度必须在6到50个字符之间"))
    import re

    pattern = r"^[a-zA-Z0-9_.-]+@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*\.[a-zA-Z0-9]{2,6}$"
    if not re.match(pattern, email):
        return DataVerify(result=False, message=_("邮箱格式错误"))
    return DataVerify(result=True, message=_("邮箱格式正确"))
