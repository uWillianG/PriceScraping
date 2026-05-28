from __future__ import annotations

from email.message import EmailMessage
import smtplib

from config import Settings
from shopping_assistant.models import DealAlert, ProductOffer


class EmailNotifier:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def render_deals_html(
        self, offers: list[ProductOffer], alerts: list[DealAlert] | None = None
    ) -> str:
        alert_rows = "".join(
            f"""
            <tr>
              <td>{alert.offer.store}</td>
              <td><a href="{alert.offer.url}">{alert.offer.title}</a></td>
              <td>R$ {alert.offer.current_price}</td>
              <td>{alert.message}</td>
            </tr>
            """
            for alert in (alerts or [])
        )
        offer_rows = "".join(
            f"""
            <tr>
              <td>{offer.store}</td>
              <td><a href="{offer.url}">{offer.title}</a></td>
              <td>R$ {offer.current_price}</td>
              <td>{offer.discount_percent or ""}</td>
            </tr>
            """
            for offer in offers
        )
        return f"""
        <!doctype html>
        <html>
        <body style="font-family: Arial, sans-serif; color: #1f2933;">
          <h2>Home Shopping Price Assistant</h2>
          <h3>Triggered alerts</h3>
          <table border="1" cellpadding="8" cellspacing="0">
            <tr><th>Store</th><th>Product</th><th>Price</th><th>Alert</th></tr>
            {alert_rows or '<tr><td colspan="4">No alerts triggered.</td></tr>'}
          </table>
          <h3>Best deals</h3>
          <table border="1" cellpadding="8" cellspacing="0">
            <tr><th>Store</th><th>Product</th><th>Price</th><th>Discount %</th></tr>
            {offer_rows or '<tr><td colspan="4">No offers found.</td></tr>'}
          </table>
        </body>
        </html>
        """

    def send_deals(
        self, offers: list[ProductOffer], alerts: list[DealAlert] | None = None
    ) -> None:
        if not (
            self.settings.smtp_host
            and self.settings.smtp_from_email
            and self.settings.smtp_to_email
        ):
            raise ValueError("SMTP settings are incomplete.")

        message = EmailMessage()
        message["Subject"] = "Best home shopping deals"
        message["From"] = self.settings.smtp_from_email
        message["To"] = self.settings.smtp_to_email
        message.set_content("Your email client does not support HTML messages.")
        message.add_alternative(
            self.render_deals_html(offers, alerts=alerts),
            subtype="html",
        )

        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as smtp:
            if self.settings.smtp_use_tls:
                smtp.starttls()
            if self.settings.smtp_username and self.settings.smtp_password:
                smtp.login(self.settings.smtp_username, self.settings.smtp_password)
            smtp.send_message(message)
