import smtplib
import ssl
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Check SMTP connectivity/auth using Django EMAIL_* settings."

    def add_arguments(self, parser):
        parser.add_argument(
            "--debug",
            action="store_true",
            help=(
                "Enable smtplib debug output. WARNING: this prints base64 auth payloads "
                "to stdout (credentials can be recovered). Use only locally and never in logs."
            ),
        )
        parser.add_argument(
            "--no-login",
            action="store_true",
            help="Only connect and EHLO (skip AUTH login).",
        )

    def handle(self, *args, **options):
        host = getattr(settings, "EMAIL_HOST", "")
        port = int(getattr(settings, "EMAIL_PORT", 0) or 0)
        username = getattr(settings, "EMAIL_HOST_USER", "")
        password = getattr(settings, "EMAIL_HOST_PASSWORD", "")
        timeout = int(getattr(settings, "EMAIL_TIMEOUT", 30) or 30)
        use_ssl = bool(getattr(settings, "EMAIL_USE_SSL", False))
        use_tls = bool(getattr(settings, "EMAIL_USE_TLS", False))

        self.stdout.write("SMTP settings (sanitized):")
        self.stdout.write(f"  EMAIL_BACKEND      = {getattr(settings, 'EMAIL_BACKEND', '')}")
        self.stdout.write(f"  EMAIL_HOST         = {host!r}")
        self.stdout.write(f"  EMAIL_PORT         = {port}")
        self.stdout.write(f"  EMAIL_USE_SSL      = {use_ssl}")
        self.stdout.write(f"  EMAIL_USE_TLS      = {use_tls}")
        self.stdout.write(f"  EMAIL_HOST_USER    = {username!r}")
        self.stdout.write(f"  EMAIL_HOST_PASSWORD= <set={bool(password)} len={len(password)}>")
        self.stdout.write(f"  DEFAULT_FROM_EMAIL = {getattr(settings, 'DEFAULT_FROM_EMAIL', '')!r}")
        self.stdout.write(f"  EMAIL_TIMEOUT      = {timeout}")

        if host != host.strip():
            self.stdout.write(self.style.WARNING("WARNING: EMAIL_HOST has leading/trailing whitespace."))
        if username != username.strip():
            self.stdout.write(self.style.WARNING("WARNING: EMAIL_HOST_USER has leading/trailing whitespace."))
        if password and password != password.strip():
            self.stdout.write(
                self.style.WARNING(
                    "WARNING: EMAIL_HOST_PASSWORD has leading/trailing whitespace (common copy/paste issue)."
                )
            )

        if use_ssl and use_tls:
            self.stdout.write(
                self.style.WARNING(
                    "WARNING: Both EMAIL_USE_SSL and EMAIL_USE_TLS are true. Django will typically prefer one; "
                    "consider setting only one explicitly."
                )
            )

        if not host or not port:
            raise SystemExit("EMAIL_HOST/EMAIL_PORT not configured.")

        if options["debug"]:
            self.stdout.write(
                self.style.WARNING(
                    "--debug enabled: credentials can be recovered from output. Do not run this on production logs."
                )
            )

        context = ssl.create_default_context()
        smtp = None
        try:
            if use_ssl:
                smtp = smtplib.SMTP_SSL(host=host, port=port, timeout=timeout, context=context)
            else:
                smtp = smtplib.SMTP(host=host, port=port, timeout=timeout)

            if options["debug"]:
                smtp.set_debuglevel(1)

            smtp.ehlo()

            if (not use_ssl) and use_tls:
                smtp.starttls(context=context)
                smtp.ehlo()

            if not options["no-login"]:
                smtp.login(username, password)
                self.stdout.write(self.style.SUCCESS("LOGIN OK"))
            else:
                self.stdout.write(self.style.SUCCESS("CONNECTED OK (no login attempted)"))

        except smtplib.SMTPAuthenticationError as exc:
            code, msg = exc.smtp_code, exc.smtp_error
            self.stdout.write(self.style.ERROR(f"AUTH FAILED: {code} {msg!r}"))
            self.stdout.write("Common causes to check:")
            self.stdout.write("  - Wrong mailbox password (cPanel email account password != cPanel login password)")
            self.stdout.write("  - Username format: try full email (user@domain) vs local part (user)")
            self.stdout.write("  - Password truncated by .env parsing if it contains '#' (wrap value in quotes)")
            self.stdout.write("  - Connecting to the wrong SMTP host for where your mailbox is actually hosted")
            raise
        finally:
            try:
                if smtp is not None:
                    smtp.quit()
            except Exception:
                pass
