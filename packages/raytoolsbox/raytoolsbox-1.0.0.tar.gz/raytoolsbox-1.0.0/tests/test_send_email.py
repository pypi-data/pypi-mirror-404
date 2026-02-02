from raytoolsbox.mailToPhone import send_email, _load_email_config
from unittest.mock import patch

def test_load_email_config_not_found():
    # 模拟加载不到配置文件
    with patch("raytoolsbox.mailToPhone.Path.exists", return_value=False):
        result = send_email()
        assert result == False

def test_send_email_failure():
    # 模拟 SMTP 出错
    with patch("raytoolsbox.mailToPhone._load_email_config", return_value={
        "smtp_server": "smtp.qq.com",
        "smtp_port": 465,
        "from_addr": "test@qq.com",
        "password": "wrong",
    }), patch("raytoolsbox.mailToPhone.smtplib.SMTP_SSL") as mock_smtp:
        mock_instance = mock_smtp.return_value
        mock_instance.login.side_effect = Exception("登录失败")

        result = send_email()
        assert result == False