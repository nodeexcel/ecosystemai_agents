import time
from app.models.model import SessionLocal
from app.services.celery_app import celery_application
from app.models.phone_agent import PhoneCampaign, CallRecord
from app.models.contacts import ContactLists, Lists, Contacts
from app.router.phone_agent import make_call

@celery_application.task
def outgoing_call_schedular():
    db = SessionLocal()
    try:
        campaigns = db.query(PhoneCampaign).all()
        count = db.query(PhoneCampaign).count()
        print(count)
        for campaign in campaigns:
            print("vbhjkjhgvbhjk")
            target_list = campaign.target_lists
            print(target_list)
            contact_list = db.query(Lists).filter_by(id=target_list).first()
            if not contact_list:
                print("vbnhjklkjh")
                continue
            contacts_in_lists = db.query(ContactLists).filter_by(lists_id=target_list).all()
            if not contacts_in_lists:
                print("ghjkl")
                continue
            for contact_in_list in contacts_in_lists:
                contact_to = db.query(Contacts).filter_by(id=contact_in_list.contactid).first()
                call_record = (db.query(CallRecord).filter_by(from_contact_number=campaign.phone_number, contact_number=contact_to.phone).first())
                if call_record:
                    print("rtyuio")
                    continue
                else:
                    call_record = {"from_contact_number": campaign.phone_number,
                               "contact_number": contact_to.phone}
                    make_call(call_record)
                    time.sleep(60)
    finally:
        db.close()
            
    
    