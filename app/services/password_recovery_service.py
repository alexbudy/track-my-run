import os

from flask import current_app, flash, url_for
from flask_mail import Message
from itsdangerous import BadTimeSignature, SignatureExpired, URLSafeTimedSerializer

from app.extensions import mail, redis_cache


class PasswordRecoveryService:
    @staticmethod
    def send_recovery_link(email: str, login: str) -> None:
        current_app.logger.info(
            f"Sending a password recovery link to {email} for {login}"
        )

        s = URLSafeTimedSerializer(os.getenv("TIMED_SERIALIZER_SECRET"))

        token = s.dumps(email, salt=os.getenv("EMAIL_SALT"))

        msg = Message(
            "Password Reset Request",
            sender="alexbudy@track-my-run.com",
            recipients=[email],
        )
        link = url_for("auth_blueprint.reset_password", token=token, _external=True)
        msg.body = f"Your link to reset your password is {link}"

        mail.send(msg)

    @staticmethod
    def verify_token(token: str) -> str:
        if redis_cache.exists(token):
            flash("Link has already been used, please create a new one", "error")
            return None

        s = URLSafeTimedSerializer(os.getenv("TIMED_SERIALIZER_SECRET"))

        try:
            email = s.loads(
                token,
                salt=os.getenv("EMAIL_SALT"),
                max_age=int(os.getenv("TOKEN_EXPIRATION_TIME_S")),
            )
        except SignatureExpired:
            flash("The link has expired, please try again", "error")
            return None
        except BadTimeSignature:
            flash("Invalid token, please try again", "error")
            return None

        return email
