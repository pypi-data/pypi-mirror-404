import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
import yaml
from pathlib import Path

def _load_email_config(provider: str)-> bool:
    # 1. 当前脚本所在目录
    local_config = Path(__file__).parent / "email_config.yaml"

    # 2. 用户主目录
    home_config = Path.home() / ".email_config.yaml"

    # 挑选存在的一个
    config_path = local_config if local_config.exists() else home_config

    if not config_path.exists():
        raise FileNotFoundError(
            f"未找到配置文件: {config_path}\n"
            "你需要手动创建，内容格式如下：\n"
            "qq:\n"
            "  smtp_server: smtp.qq.com\n"
            "  smtp_port: 465\n"
            "  from_addr: your@qq.com\n"
            "  password: your_auth_code"
        )

    with open(config_path, "r", encoding="utf-8") as f:
        all_config = yaml.safe_load(f)
    return all_config[provider]


def send_email(
        subject: str='HelloWorld', 
        content: str='这是一个测试邮件', 
        to_addr: str='',
        serverName: str='',
        use_smtp:str='qq') -> None:
    """
    :param subject: 邮件主题 
    :param content: 邮件内容
    :param to_addr: 接收邮箱地址
    :param serverName: 服务器名称
    :param use_smtp: 使用的SMTP服务提供商
    """
    try:
        config = _load_email_config(use_smtp)
    except Exception as e:
        print(f"加载配置失败: {e}")
        return False

    smtp_server = config['smtp_server']
    smtp_port = config['smtp_port']
    from_addr = config['from_addr']
    password = config['password']

    nickname = serverName  # 这里自定义你的备注
    if not to_addr:
        to_addr=from_addr  # 如果没有指定收件人，则发给自己
    
    message = MIMEText(content, 'html', 'utf-8')
    # 用 formataddr，可以自动支持中文昵称
    message['From'] = formataddr((str(Header(nickname, 'utf-8')), from_addr))
    message['To'] = Header(to_addr)
    message['Subject'] = Header(subject, 'utf-8')
    
    try:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(from_addr, password)
        server.sendmail(from_addr, [to_addr], message.as_string())
        server.quit()
        print('消息发送成功！')
        return True
    except Exception as e:
        print('发送失败:', e)
        return False

# 下面按你的用法
if __name__ == '__main__':
    print(send_email())