from app.services.ingestion.gmail_service import GmailService

service = GmailService()
emails = service.get_unread_emails()

for e in emails:
    print("Sender:", e["sender"])
    print("Subject:", e["subject"])
    print("Body:", e["body"][:200])
    print("-" * 80)
