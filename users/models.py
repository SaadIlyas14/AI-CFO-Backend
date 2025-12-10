# users/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from companies.models import CompanyUser

class User(AbstractUser):
    is_company = models.BooleanField(default=False)
    is_company_user = models.BooleanField(default=False)
    softdelete = models.BooleanField(default=False)
    reset_token = models.CharField(max_length=64, blank=True, null=True)

    def get_company(self):
        if self.is_company:
            try:
                return self.company_profile  # from companies.Company
            except:
                return None
        elif self.is_company_user:
            try:
                return self.companyuser.company  # from companies.CompanyUser
            except CompanyUser.DoesNotExist:
                return None
        return None
