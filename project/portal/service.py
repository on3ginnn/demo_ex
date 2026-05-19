from __future__ import annotations
from typing import Optional
from .models import Application


class ApplicationLifecycle:
    _CHAIN = (
        Application.Status.NEW.value,
        Application.Status.IN_PROGRESS.value,
        Application.Status.COMPLETED.value,
    )

    @classmethod
    def next_status(cls, current):
        try:
            idx = cls._CHAIN.index(current)
        except ValueError:
            return None
        if idx + 1 >= len(cls._CHAIN):
            return None
        return cls._CHAIN[idx + 1]

    @classmethod
    def advance(cls, application):
        nxt = cls.next_status(application.status)
        if nxt is None:
            return None
        application.status = nxt
        application.save(update_fields=['status'])
        return nxt

    @classmethod
    def set_status(cls, application, new_status):
        allowed = {s.value for s in Application.Status}
        if new_status not in allowed:
            return False
        if application.status == new_status:
            return False
        application.status = new_status
        application.save(update_fields=['status'])
        return True
