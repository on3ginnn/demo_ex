from django.contrib import messages
from django.shortcuts import redirect


class StaffSessionRequiredMixin:

    staff_login_url = 'portal:staff_login'

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('staff_authenticated'):
            messages.warning(request, 'Войдите в панель администратора.')
            return redirect(self.staff_login_url)
        return super().dispatch(request, *args, **kwargs)
