import os
import smtplib
from datetime import date, timedelta
from email.message import EmailMessage
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import Application, NotificationDelivery, NotificationPreference, Opportunity


def get_preferences(db, user):
    preferences = user.notification_preferences
    if not preferences:
        preferences = NotificationPreference(user_id=user.id)
        db.add(preferences)
        db.flush()
    return preferences


def deadline_items(db, user, days=7):
    cutoff = date.today() + timedelta(days=days)
    return (
        db.query(Opportunity)
        .join(Application, Application.opportunity_id == Opportunity.id)
        .filter(
            Application.user_id == user.id,
            Application.status.in_(["saved", "applied", "interview"]),
            Opportunity.deadline >= date.today(),
            Opportunity.deadline <= cutoff,
        )
        .order_by(Opportunity.deadline.asc())
        .all()
    )


def digest_items(db, user):
    return (
        db.query(Application)
        .filter(Application.user_id == user.id, Application.status.notin_(["rejected", "withdrawn"]))
        .order_by(Application.updated_at.desc())
        .limit(10)
        .all()
    )


def deadline_body(opportunities):
    lines = ["Upcoming deadlines in your Oppora tracker:"]
    lines.extend(f"- {op.title} at {op.organization}: {op.deadline.isoformat()}" for op in opportunities)
    return "\n".join(lines)


def digest_body(applications):
    lines = ["Your Oppora application digest:"]
    lines.extend(f"- {item.opportunity.title} at {item.opportunity.organization}: {item.status}" for item in applications)
    return "\n".join(lines)


def _send_email(user, subject, body):
    host = os.getenv("SMTP_HOST")
    if not host:
        return "preview"
    message = EmailMessage()
    message["From"] = os.getenv("SMTP_FROM", user.email)
    message["To"] = user.email
    message["Subject"] = subject
    message.set_content(body)
    with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", "587"))) as server:
        server.starttls()
        username = os.getenv("SMTP_USERNAME")
        if username:
            server.login(username, os.getenv("SMTP_PASSWORD", ""))
        server.send_message(message)
    return "sent"


def _send_telegram(preferences, body):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or not preferences.telegram_chat_id:
        return "preview"
    payload = urlencode({"chat_id": preferences.telegram_chat_id, "text": body}).encode()
    request = Request(f"https://api.telegram.org/bot{token}/sendMessage", data=payload, method="POST")
    with urlopen(request, timeout=10) as response:
        if response.status >= 300:
            raise RuntimeError(f"Telegram returned {response.status}")
    return "sent"


def deliver(db, user, notification_type, subject, body):
    preferences = get_preferences(db, user)
    channels = []
    if preferences.email_enabled:
        channels.append(("email", lambda: _send_email(user, subject, body)))
    if preferences.telegram_enabled:
        channels.append(("telegram", lambda: _send_telegram(preferences, body)))
    deliveries = []
    for channel, sender in channels:
        try:
            status = sender()
        except Exception:
            status = "failed"
        delivery = NotificationDelivery(
            user_id=user.id,
            channel=channel,
            notification_type=notification_type,
            subject=subject,
            body=body,
            status=status,
        )
        db.add(delivery)
        deliveries.append(delivery)
    db.commit()
    return deliveries