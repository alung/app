from app.config import (
    MAX_ACTIVITY_DURING_MINUTE_PER_ALIAS,
    MAX_ACTIVITY_DURING_MINUTE_PER_MAILBOX,
)
from app.extensions import db
from app.email.rate_limit import (
    rate_limited_forward_phase,
    rate_limited_for_alias,
    rate_limited_for_mailbox,
    rate_limited_reply_phase,
)
from app.models import User, Alias, EmailLog, Contact


def test_rate_limited_forward_phase_for_alias(flask_client):
    user = User.create(
        email="a@b.c", password="password", name="Test User", activated=True
    )
    db.session.commit()

    # no rate limiting for a new alias
    alias = Alias.create_new_random(user)
    db.session.commit()
    assert not rate_limited_for_alias(alias)

    # rate limit when there's a previous activity on alias
    contact = Contact.create(
        user_id=user.id,
        alias_id=alias.id,
        website_email="contact@example.com",
        reply_email="rep@sl.local",
    )
    db.session.commit()
    for _ in range(MAX_ACTIVITY_DURING_MINUTE_PER_ALIAS + 1):
        EmailLog.create(user_id=user.id, contact_id=contact.id)
        db.session.commit()

    assert rate_limited_for_alias(alias)


def test_rate_limited_forward_phase_for_mailbox(flask_client):
    user = User.create(
        email="a@b.c", password="password", name="Test User", activated=True
    )
    db.session.commit()

    alias = Alias.create_new_random(user)
    db.session.commit()

    contact = Contact.create(
        user_id=user.id,
        alias_id=alias.id,
        website_email="contact@example.com",
        reply_email="rep@sl.local",
    )
    db.session.commit()
    for _ in range(MAX_ACTIVITY_DURING_MINUTE_PER_MAILBOX + 1):
        EmailLog.create(user_id=user.id, contact_id=contact.id)
        db.session.commit()

    EmailLog.create(user_id=user.id, contact_id=contact.id)

    # Create another alias with the same mailbox
    # will be rate limited as there's a previous activity on mailbox
    alias2 = Alias.create_new_random(user)
    db.session.commit()
    assert rate_limited_for_mailbox(alias2)


def test_rate_limited_forward_phase(flask_client):
    # no rate limiting when alias does not exist
    assert not rate_limited_forward_phase("not-exist@alias.com")


def test_rate_limited_reply_phase(flask_client):
    # no rate limiting when reply_email does not exist
    assert not rate_limited_reply_phase("not-exist-reply@alias.com")

    user = User.create(
        email="a@b.c", password="password", name="Test User", activated=True
    )
    db.session.commit()

    alias = Alias.create_new_random(user)
    db.session.commit()

    contact = Contact.create(
        user_id=user.id,
        alias_id=alias.id,
        website_email="contact@example.com",
        reply_email="rep@sl.local",
    )
    db.session.commit()
    for _ in range(MAX_ACTIVITY_DURING_MINUTE_PER_ALIAS + 1):
        EmailLog.create(user_id=user.id, contact_id=contact.id)
        db.session.commit()

    assert rate_limited_reply_phase("rep@sl.local")
