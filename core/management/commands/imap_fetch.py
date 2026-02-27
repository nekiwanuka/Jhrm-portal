import imaplib
import re
from email import policy
from email.header import decode_header, make_header
from email.parser import BytesParser
from email.utils import getaddresses, parsedate_to_datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.urls import reverse

from audit.models import AuditLog, Notification
from core.models import InboxState, InboundEmail, InboundEmailAttachment


_UIDVALIDITY_RE = re.compile(r"UIDVALIDITY\s+(\d+)")


def _admin_recipients():
    User = get_user_model()
    return list(User.objects.filter(Q(is_superuser=True) | Q(role__in={'SUPER_ADMIN', 'HR_MANAGER'})).only('id'))


def _decode_mime_words(value: str) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def _extract_address_list(header_value: str) -> str:
    addresses = getaddresses([header_value or ""]) if header_value else []
    cleaned = []
    for name, addr in addresses:
        name = (name or "").strip()
        addr = (addr or "").strip()
        if not addr:
            continue
        cleaned.append(f"{name} <{addr}>".strip() if name else addr)
    return ", ".join(cleaned)


def _get_from_name_email(header_value: str):
    addresses = getaddresses([header_value or ""]) if header_value else []
    if not addresses:
        return "", ""
    name, addr = addresses[0]
    return (name or "").strip(), (addr or "").strip()


def _safe_filename(name: str) -> str:
    name = (name or "attachment").strip()
    name = name.replace("\\", "_").replace("/", "_")
    return name[:180] or "attachment"


def _extract_text_body(message) -> str:
    # Prefer text/plain parts that are not attachments.
    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            if content_type != "text/plain":
                continue
            content_disposition = (part.get("Content-Disposition") or "").lower()
            if "attachment" in content_disposition:
                continue
            try:
                payload = part.get_payload(decode=True) or b""
                charset = part.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="replace")
            except Exception:
                continue
    else:
        if message.get_content_type() == "text/plain":
            try:
                payload = message.get_payload(decode=True) or b""
                charset = message.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="replace")
            except Exception:
                return ""

    # Fallback: if only HTML exists, store empty (minimal UI).
    return ""


class Command(BaseCommand):
    help = "Fetch inbound emails from IMAP and store them for the portal inbox."

    def add_arguments(self, parser):
        parser.add_argument("--mailbox", default=None, help="IMAP mailbox to read (default from settings.IMAP_MAILBOX)")
        parser.add_argument("--max", type=int, default=None, help="Max messages to fetch per run (default from settings.IMAP_MAX_FETCH)")

    def handle(self, *args, **options):
        mailbox = options["mailbox"] or getattr(settings, "IMAP_MAILBOX", "INBOX")
        max_fetch = options["max"] or int(getattr(settings, "IMAP_MAX_FETCH", 50) or 50)

        host = getattr(settings, "IMAP_HOST", "")
        port = int(getattr(settings, "IMAP_PORT", 993) or 993)
        username = getattr(settings, "IMAP_USER", "")
        password = getattr(settings, "IMAP_PASSWORD", "")
        use_ssl = bool(getattr(settings, "IMAP_USE_SSL", True))

        if not host or not username or not password:
            raise SystemExit("IMAP is not configured. Set IMAP_HOST, IMAP_USER, IMAP_PASSWORD in your environment.")

        self.stdout.write(f"Connecting to IMAP {host}:{port} mailbox={mailbox} ssl={use_ssl}...")

        imap = None
        try:
            imap = imaplib.IMAP4_SSL(host, port) if use_ssl else imaplib.IMAP4(host, port)
            imap.login(username, password)

            typ, data = imap.select(mailbox, readonly=True)
            if typ != "OK":
                raise SystemExit(f"Could not select mailbox {mailbox!r}: {data}")

            # Extract UIDVALIDITY from SELECT response.
            uidvalidity = 0
            for line in (imap.response("UIDVALIDITY")[1] or []):
                if not line:
                    continue
                match = _UIDVALIDITY_RE.search(line.decode("utf-8", errors="ignore"))
                if match:
                    uidvalidity = int(match.group(1))
                    break

            state, _ = InboxState.objects.get_or_create(mailbox=mailbox)
            if uidvalidity and state.uidvalidity and uidvalidity != state.uidvalidity:
                # Mailbox was recreated; reset UID tracking.
                state.last_uid = 0
            if uidvalidity:
                state.uidvalidity = uidvalidity

            start_uid = int(state.last_uid or 0) + 1

            typ, search_data = imap.uid("search", None, f"(UID {start_uid}:*)")
            if typ != "OK":
                raise SystemExit(f"UID SEARCH failed: {search_data}")

            uid_list = (search_data[0] or b"").split()
            if not uid_list:
                self.stdout.write("No new messages.")
                return

            # Limit the run.
            uid_list = uid_list[:max_fetch]

            fetched = 0
            max_uid_seen = int(state.last_uid or 0)

            for uid_bytes in uid_list:
                uid = int(uid_bytes)
                if uid > max_uid_seen:
                    max_uid_seen = uid

                exists = InboundEmail.objects.filter(mailbox=mailbox, uid=uid).exists()
                if exists:
                    continue

                typ, fetch_data = imap.uid("fetch", uid_bytes, "(RFC822)")
                if typ != "OK" or not fetch_data or not fetch_data[0]:
                    continue

                raw_bytes = fetch_data[0][1]
                message = BytesParser(policy=policy.default).parsebytes(raw_bytes)

                subject = _decode_mime_words(message.get("Subject", ""))
                from_name, from_email = _get_from_name_email(message.get("From", ""))
                to = _extract_address_list(message.get("To", ""))
                cc = _extract_address_list(message.get("Cc", ""))

                message_id = (message.get("Message-ID", "") or "").strip()
                in_reply_to = (message.get("In-Reply-To", "") or "").strip()
                references = (message.get("References", "") or "").strip()

                sent_at = None
                try:
                    sent_at = parsedate_to_datetime(message.get("Date")) if message.get("Date") else None
                except Exception:
                    sent_at = None

                body_text = _extract_text_body(message)

                with transaction.atomic():
                    inbound = InboundEmail.objects.create(
                        mailbox=mailbox,
                        uid=uid,
                        message_id=message_id[:255],
                        in_reply_to=in_reply_to[:255],
                        references=references,
                        subject=(subject or "")[:255],
                        from_name=(from_name or "")[:255],
                        from_email=(from_email or "")[:255],
                        to=to,
                        cc=cc,
                        sent_at=sent_at,
                        body_text=body_text,
                    )

                    # Save attachments (minimal: only real attachments).
                    attachment_count = 0
                    max_attachments = 10
                    max_attachment_bytes = 10 * 1024 * 1024

                    for part in message.walk():
                        if attachment_count >= max_attachments:
                            break

                        filename = part.get_filename()
                        content_disposition = (part.get("Content-Disposition") or "").lower()
                        if not filename and "attachment" not in content_disposition:
                            continue

                        filename = _safe_filename(_decode_mime_words(filename or "attachment"))
                        payload = part.get_payload(decode=True)
                        if not payload:
                            continue
                        if len(payload) > max_attachment_bytes:
                            continue

                        content_type = part.get_content_type() or "application/octet-stream"

                        attachment = InboundEmailAttachment(
                            email=inbound,
                            filename=filename,
                            content_type=content_type[:120],
                            size=len(payload),
                        )
                        attachment.file.save(filename, ContentFile(payload), save=True)
                        attachment_count += 1

                fetched += 1

            # Persist progress even if some messages were skipped.
            state.last_uid = max(state.last_uid, max_uid_seen)
            state.save(update_fields=["uidvalidity", "last_uid", "updated_at"])

            if fetched:
                try:
                    inbox_path = reverse('core:inbox')
                except Exception:
                    inbox_path = '/tools/inbox/'

                try:
                    AuditLog.objects.create(
                        user=None,
                        action=f'EMAIL FETCH: {fetched} ({mailbox})'[:100],
                        path=inbox_path,
                        method='IMAP',
                        status_code=200,
                    )
                except Exception:
                    pass

                try:
                    admins = _admin_recipients()
                    if admins:
                        Notification.objects.bulk_create(
                            [
                                Notification(
                                    recipient=a,
                                    actor=None,
                                    message=f'New inbound email(s): {fetched} fetched in {mailbox}'[:255],
                                    path=inbox_path,
                                    level=Notification.LEVEL_INFO,
                                )
                                for a in admins
                            ]
                        )
                except Exception:
                    pass

            self.stdout.write(self.style.SUCCESS(f"Fetched {fetched} message(s). last_uid={state.last_uid}"))

        finally:
            if imap is not None:
                try:
                    imap.logout()
                except Exception:
                    pass
