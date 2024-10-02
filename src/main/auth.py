import logging

import mozilla_django_oidc.auth
from django.contrib.auth.models import Group
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse

log = logging.getLogger(__name__)

def oidc_login(request, **kwargs):
    oidc_authentication_init = reverse("oidc_authentication_init")
    redirect = f'{oidc_authentication_init}?next={request.GET.get("next", "")}'
    return HttpResponseRedirect(redirect)


class OIDCAuthenticationBackend(mozilla_django_oidc.auth.OIDCAuthenticationBackend):
    def verify_claims(self, claims):
        verified = super(OIDCAuthenticationBackend, self).verify_claims(claims)
        has_roles = claims.get("roles")
        return verified and has_roles

    def create_user(self, claims):
        user = super(OIDCAuthenticationBackend, self).create_user(claims)
        return self.update_user(user, claims)

    def update_user(self, user, claims):
        user.first_name = claims.get("given_name", "")
        user.last_name = claims.get("family_name", "")
        user.save()
        self.update_groups(user, claims)
        return user

    def update_groups(self, user, claims):
        """
        We can use this method to update the groups of the user
        based on the roles passed by Azure AD. At the moment we receive none,
        and we assume any user that is able log in is an admin.
        """

        with transaction.atomic():
            # standard zero permissions shows only home-admin-page with mention: You don’t have permission to view or edit anything.
            user.groups.clear()
            user.is_staff = True
            user.is_superuser = False

            for role in claims["roles"]:
                match role[16:]:  # match without "environment-app_name-"
                    case "app-admin-maintainers":
                        django_group_name = role[26:]
                        try:
                            group = Group.objects.get(name=django_group_name)
                            user.groups.add(group)
                        except:
                            pass    
                    case "application-admin":
                        user.is_superuser = True

            user.save()

    def authenticate(self, request, **kwargs):
        user = super().authenticate(request, **kwargs)
        # Ensure that the user does not come into an endless redirect loop
        # when they try to login in to the admin, but do not have the correct
        # role to edit admin-models.
        if user and user.is_staff:
            return user
        return None

    def get_userinfo(self, access_token, id_token, payload):
        """Return user details dictionary. The id_token and payload are not used in
        the default implementation, but may be used when overriding this method"""

        user_response = super().get_userinfo(access_token, id_token, payload)

        # Add 'roles', 'groups' etc from payload
        if payload.get("roles"):
            user_response["roles"] = payload["roles"]

        return user_response
