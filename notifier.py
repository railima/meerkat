"""Notificações nativas. Windows: winotify (clique abre o PR). macOS: UserNotifications quando empacotado
(clique abre o PR); fora do .app, osascript (sem clique)."""

import subprocess
import sys
import uuid
import webbrowser
from pathlib import Path

ICON = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / "icon" / "icon.png"
_center = None  # UNUserNotificationCenter, configurado em setup()


def setup():
    """Chamar uma vez, na thread principal, com o app já rodando."""
    global _center
    if sys.platform != "darwin" or not getattr(sys, "frozen", False):
        return
    try:
        import objc
        from Foundation import NSObject
        from UserNotifications import (
            UNAuthorizationOptionAlert,
            UNAuthorizationOptionSound,
            UNNotificationPresentationOptionBanner,
            UNNotificationPresentationOptionList,
            UNUserNotificationCenter,
        )

        class Delegate(NSObject):
            def userNotificationCenter_didReceiveNotificationResponse_withCompletionHandler_(self, c, response, done):
                url = response.notification().request().content().userInfo().get("url")
                if url:
                    webbrowser.open(url)
                done()

            def userNotificationCenter_willPresentNotification_withCompletionHandler_(self, c, n, done):
                done(UNNotificationPresentationOptionBanner | UNNotificationPresentationOptionList)

        center = UNUserNotificationCenter.currentNotificationCenter()
        setup.delegate = Delegate.alloc().init()  # referência forte: o centro guarda o delegate como weak
        center.setDelegate_(setup.delegate)
        center.requestAuthorizationWithOptions_completionHandler_(
            UNAuthorizationOptionAlert | UNAuthorizationOptionSound, lambda granted, error: None)
        _center = center
    except Exception:  # sem bundle/permissão: cai no osascript
        _center = None


def notify(title, body, url=None):
    if sys.platform == "win32":
        from winotify import Notification

        toast = Notification(app_id="Meerkat", title=title, msg=body, launch=url or "",
                             icon=str(ICON) if ICON.exists() else "")
        toast.show()
    elif sys.platform == "darwin":
        if _center is not None:
            from UserNotifications import UNMutableNotificationContent, UNNotificationRequest, UNNotificationSound

            content = UNMutableNotificationContent.alloc().init()
            content.setTitle_(title)
            content.setBody_(body)
            content.setSound_(UNNotificationSound.defaultSound())
            content.setUserInfo_({"url": url or ""})
            request = UNNotificationRequest.requestWithIdentifier_content_trigger_(str(uuid.uuid4()), content, None)
            _center.addNotificationRequest_withCompletionHandler_(request, None)
        else:
            script = "display notification item 2 of argv with title item 1 of argv"
            subprocess.run(["osascript", "-e", f"on run argv\n{script}\nend run", title, body], check=False)
