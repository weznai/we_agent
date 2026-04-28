import json
import smtplib
import ssl
import time
import uuid

import markdown as md_lib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

from langchain_core.tools import tool as lc_tool

from ..utils.logger import get_logger
from ..config import get_settings
from .registry import register

logger = get_logger(__name__)


def _build_smtp_config():
    settings = get_settings()
    return {
        "host": settings.SMTP_HOST,
        "port": settings.SMTP_PORT,
        "user": settings.SMTP_USER,
        "password": settings.SMTP_PASSWORD,
        "from_addr": settings.SMTP_FROM or settings.SMTP_USER,
    }


def _send_smtp(subject: str, html_content: str, receiver_emails: list[str]) -> str:
    cfg = _build_smtp_config()

    message = MIMEMultipart("alternative")
    message.attach(MIMEText(html_content, "html", "utf-8"))

    message["From"] = Header("WeAgent智能助手", "utf-8")
    message["To"] = ", ".join(receiver_emails)
    message["Subject"] = Header(subject, "utf-8")
    message["X-Priority"] = "3"
    message["X-Mailer"] = "WeAgent System"
    message["Message-ID"] = f"<{uuid.uuid4()}@weagent.com>"

    try:
        logger.info(
            f"[Mail] Connecting to {cfg['host']}:{cfg['port']} "
            f"for sending to {receiver_emails}"
        )
        smtp_obj = None
        last_err = None
        for attempt in range(3):
            try:
                smtp_obj = smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=30)
                break
            except (smtplib.SMTPServerDisconnected, smtplib.SMTPException, OSError) as e:
                last_err = e
                logger.warning(f"[Mail] Connect attempt {attempt+1}/3 failed: {e}")
                if attempt < 2:
                    time.sleep(1)
        if smtp_obj is None:
            raise last_err
        smtp_obj.login(cfg["user"], cfg["password"])
        result = smtp_obj.sendmail(cfg["from_addr"], receiver_emails, message.as_string())
        smtp_obj.quit()

        if result:
            logger.warning(f"[Mail] Partial failure for recipients: {result}")
            return json.dumps(
                {"success": False, "message": f"部分收件人发送失败: {result}"},
                ensure_ascii=False,
            )

        logger.info(f"[Mail] Sent successfully to {receiver_emails}")
        return json.dumps(
            {"success": True, "message": f"邮件已成功发送至 {', '.join(receiver_emails)}"},
            ensure_ascii=False,
        )
    except smtplib.SMTPRecipientsRefused as e:
        err = f"收件人被拒绝: {e}"
        logger.error(f"[Mail] {err}")
        return json.dumps({"success": False, "message": err}, ensure_ascii=False)
    except smtplib.SMTPSenderRefused as e:
        err = f"发件人被拒绝: {e}"
        logger.error(f"[Mail] {err}")
        return json.dumps({"success": False, "message": err}, ensure_ascii=False)
    except smtplib.SMTPException as e:
        err = f"SMTP错误: {e}"
        logger.error(f"[Mail] {err}")
        return json.dumps({"success": False, "message": err}, ensure_ascii=False)
    except Exception as e:
        err = f"发送异常: {e}"
        logger.error(f"[Mail] {err}")
        return json.dumps({"success": False, "message": err}, ensure_ascii=False)


@lc_tool
def send_email(
    subject: str,
    content: str,
    receiver_email: str = "",
    content_type: str = "markdown",
) -> str:
    """发送邮件。支持将Markdown内容自动转换为格式化的HTML邮件发送给指定收件人。

    Args:
        subject: 邮件主题
        content: 邮件内容，支持Markdown格式或纯文本
        receiver_email: 收件人邮箱地址，多个收件人用英文逗号分隔。为空时使用系统默认收件人
        content_type: 内容类型，"markdown" 或 "text"，默认 "markdown"
    """
    logger.info(
        f"[Tool send_email] Invoked: subject={subject}, "
        f"receiver={receiver_email}, content_type={content_type}"
    )

    cfg = _build_smtp_config()
    if not cfg["user"] or not cfg["password"]:
        return json.dumps(
            {"success": False, "message": "邮件服务未配置（SMTP_USER / SMTP_PASSWORD）"},
            ensure_ascii=False,
        )

    if receiver_email:
        recipients = [e.strip() for e in receiver_email.split(",") if e.strip()]
    else:
        recipients = [cfg["from_addr"]]

    if not recipients:
        return json.dumps(
            {"success": False, "message": "未指定收件人邮箱"},
            ensure_ascii=False,
        )

    if content_type == "markdown":
        html_content = md_lib.markdown(content, extensions=["tables"])
    else:
        html_content = content.replace("\n", "<br>")

    return _send_smtp(subject, html_content, recipients)


register(
    name="send_email",
    tool=send_email,
    description="发送邮件，支持Markdown内容自动转HTML",
    status_msg="正在发送邮件...",
    agents=["*"],
)
