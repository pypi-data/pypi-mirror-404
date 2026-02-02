import smtplib
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict

from kalorda.database.database import SystemConfigDB
from kalorda.utils.i18n import _, t
from kalorda.utils.logger import logger


def send_email(to_email, subject, content) -> Dict[str, Any]:
    """
    发送邮件
    :param subject: 邮件主题
    :param content: 邮件内容
    :param to_email: 接收人邮箱
    :return:
    """

    # 从数据库系统配置中加载SMTP配置
    smtp_host, smtp_port, smtp_user, smtp_password = load_smtp_config()

    email_sender = EmailSender(smtp_host, smtp_port, smtp_user, smtp_password)
    return email_sender.email_send(to_email, subject, content)


def load_smtp_config():
    """
    从数据库系统配置中加载SMTP配置
    :return: smtp_host, smtp_port, smtp_user, smtp_password
    """
    db_config = SystemConfigDB.select().where(SystemConfigDB.config_key == "smtp_host").first()
    smtp_host = db_config.config_value
    db_config = SystemConfigDB.select().where(SystemConfigDB.config_key == "smtp_port").first()
    smtp_port = db_config.config_value
    db_config = SystemConfigDB.select().where(SystemConfigDB.config_key == "smtp_user").first()
    smtp_user = db_config.config_value
    db_config = SystemConfigDB.select().where(SystemConfigDB.config_key == "smtp_password").first()
    smtp_password = db_config.config_value
    return smtp_host, smtp_port, smtp_user, smtp_password


class EmailSender:
    def __init__(self, smtp_host, smtp_port, smtp_user, smtp_password):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password

    def email_send(self, to_email, subject, content) -> Dict[str, Any]:
        if not to_email:
            return {"status": False, "message": _("邮箱不能为空")}
        if not self.smtp_host or not self.smtp_port or not self.smtp_user or not self.smtp_password:
            return {"status": False, "message": _("管理员尚未配置系统SMTP，邮件发送失败")}

        msg_from = self.smtp_user  # 发送方邮箱
        msg_to = to_email  # 收件人邮箱
        subject = subject  # 主题
        content = content  # 邮件内容

        is_html_content = content.startswith("<html") or content.startswith("<!DOCTYPE html>")

        msg = MIMEMultipart("alternative") if is_html_content else MIMEText(content, "plain", "utf-8")
        if is_html_content:
            msg.attach(MIMEText(content, "html", "utf-8"))

        msg["Subject"] = Header(subject, "utf-8")
        msg["From"] = msg_from
        msg["To"] = msg_to

        try:
            smtp = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            smtp.login(self.smtp_user, self.smtp_password)
            smtp.sendmail(msg_from, msg_to, msg.as_bytes() if is_html_content else msg.as_string())
            return {"status": True, "message": _("邮件发送成功")}
        except Exception as e:
            logger.error(f"系统异常，邮件发送失败: {str(e)}")
            return {"status": False, "message": _("系统异常，邮件发送失败")}
        finally:
            if not smtp:
                smtp.quit()
