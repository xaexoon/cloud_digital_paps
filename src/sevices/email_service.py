import os
from datetime import datetime
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from email import encoders


class EmailService:
    def __init__(self):
        # ✅ 초기화 시점이 아닌 사용 시점에 환경변수 읽기
        self._smtp_server = None
        self._smtp_port = None
        self._sender_email = None
        self._sender_password = None

    @property
    def smtp_server(self):
        if self._smtp_server is None:
            self._smtp_server = os.getenv("SMTP_SERVER")
        return self._smtp_server

    @property
    def smtp_port(self):
        if self._smtp_port is None:
            port_str = os.getenv("SMTP_PORT", "587")
            self._smtp_port = int(port_str)
        return self._smtp_port

    @property
    def sender_email(self):
        if self._sender_email is None:
            self._sender_email = os.getenv("SENDER_EMAIL")
        return self._sender_email

    @property
    def sender_password(self):
        if self._sender_password is None:
            self._sender_password = os.getenv("SENDER_PASSWORD")
        return self._sender_password

    def is_configured(self) -> bool:
        configured = all([
            self.smtp_server,
            self.smtp_port,
            self.sender_email,
            self.sender_password
        ])

        # 디버깅용 로그 (설정 실패 시에만)
        if not configured:
            print(f"❌ 이메일 설정 누락:")
            print(f"   SMTP_SERVER: {self.smtp_server}")
            print(f"   SMTP_PORT: {self.smtp_port}")
            print(f"   SENDER_EMAIL: {self.sender_email}")
            print(f"   SENDER_PASSWORD: {'***' if self.sender_password else None}")

        return configured

    def create_html_body(self) -> str:
        body = f"""
                <html>
                    <body style="font-family: Arial, sans-serif; padding: 20px;">
                        <h2 style="color: #333;">{datetime.now().strftime('%Y년 %m월 %d일')}</h2>

                        <p>디지털 팝스 결과입니다</p>
                        <br>
                        <p>첨부 파일을 확인해주세요</p>                    
                        <br>
                        <p>감사합니다.</p>
                    </body>
                </html>
                """
        return body

    def send_email(self, to_email: str, subject: str, body: str, file_path: str = None, origin_file_name: str = None):
        if not self.is_configured():
            raise Exception("이메일 설정이 완료되지 않았습니다.")

        server = None

        try:
            print(f"📧 이메일 전송 준비")
            print(f"   발신자: {self.sender_email}")
            print(f"   수신자: {to_email}")
            print(f"   SMTP: {self.smtp_server}:{self.smtp_port}")

            msg = MIMEMultipart()
            msg["From"] = self.sender_email
            msg["To"] = to_email
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "html"))

            if file_path and os.path.exists(file_path):
                try:
                    with open(file_path, "rb") as f:
                        file_data = f.read()

                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(file_data)
                    encoders.encode_base64(part)

                    # ✅ 원본 파일명이 있으면 사용, 없으면 파일 경로에서 추출
                    filename = origin_file_name if origin_file_name else os.path.basename(file_path)

                    part.add_header(
                        "Content-Disposition",
                        f'attachment; filename="{filename}"'
                    )

                    msg.attach(part)
                    print(f"   ✅ 파일 첨부: {filename}")
                    if origin_file_name:
                        print(f"   📝 원본 파일명 사용: {origin_file_name}")
                        print(f"   📂 실제 파일 경로: {file_path}")

                except Exception as attach_error:
                    print(f"   ❌ 파일 첨부 실패: {str(attach_error)}")
            else:
                if file_path:
                    print(f"   ⚠️ 파일을 찾을 수 없습니다: {file_path}")

            print(f"   🔌 SMTP 서버 연결 중...")
            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30)
            server.set_debuglevel(0)
            server.starttls()

            print(f"   🔐 인증 중...")
            server.login(self.sender_email, self.sender_password)

            print(f"   📤 이메일 전송 중...")
            server.sendmail(self.sender_email, to_email, msg.as_string())

            print(f"   ✅ 이메일 전송 완료!")

            return True
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ 이메일 인증 실패: {str(e)}")
            raise Exception(f"이메일 인증 실패: {str(e)}")
        except smtplib.SMTPException as e:
            print(f"❌ SMTP 오류: {str(e)}")
            raise Exception(f"SMTP 오류: {str(e)}")
        except Exception as e:
            print(f"❌ 이메일 전송 실패: {str(e)}")
            raise Exception(f"이메일 전송 실패: {str(e)}")
        finally:
            if server:
                try:
                    server.quit()
                    print(f"   🔌 SMTP 서버 연결 종료")
                except:
                    pass


email_service = EmailService()