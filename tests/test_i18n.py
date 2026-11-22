import i18n
from events import Event
from tests.test_model import make_pr


def test_both_languages_have_the_same_keys():
    assert i18n.STRINGS["en"].keys() == i18n.STRINGS["pt-BR"].keys()


def test_ago():
    assert i18n.ago(30, "en") == "now"
    assert i18n.ago(5 * 60, "en") == "5m"
    assert i18n.ago(3 * 3600, "pt-BR") == "3h"
    assert i18n.ago(2 * 86400, "pt-BR") == "2d"


def test_notification_texts():
    pr = make_pr(repo="acme/api", number=46, title="Pix")
    title, body = i18n.notification(Event("parent_merged", pr, 45), "en")
    assert title == "Rebase needed"
    assert body == "api#46 Pix — parent #45 was merged"
    title, body = i18n.notification(Event("review_requested", pr), "pt-BR")
    assert title == "Revisão pedida"
    assert body == "api#46 Pix — por ana"
