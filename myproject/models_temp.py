# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class TestappBankaccount(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    bank = models.CharField(max_length=4)
    account_number = models.CharField(max_length=30)
    accounting_number = models.CharField(max_length=10)
    journal_number = models.CharField(max_length=2)
    city = models.CharField(max_length=100)
    account_type = models.CharField(max_length=15)
    is_active = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'testapp_bankaccount'


class TestappCheck(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    position = models.CharField(max_length=10)
    creation_date = models.DateField()
    payment_due = models.DateField(blank=True, null=True)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    observation = models.TextField()
    delivered = models.IntegerField()
    paid = models.IntegerField()
    delivered_at = models.DateTimeField(blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    cancellation_reason = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20)
    rejection_reason = models.CharField(max_length=50, blank=True, null=True)
    rejection_note = models.TextField()
    rejection_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'testapp_check'


class TestappChecker(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    code = models.CharField(unique=True, max_length=10)
    type = models.CharField(max_length=3)
    num_pages = models.IntegerField()
    index = models.CharField(max_length=3)
    starting_page = models.IntegerField()
    final_page = models.IntegerField()
    current_position = models.IntegerField()
    is_active = models.IntegerField()
    owner = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'testapp_checker'


class TestappExportrecord(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    exported_at = models.DateTimeField()
    filename = models.CharField(max_length=255)
    note = models.TextField()

    class Meta:
        managed = False
        db_table = 'testapp_exportrecord'


class TestappInvoice(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    ref = models.CharField(unique=True, max_length=50)
    date = models.DateField()
    status = models.CharField(max_length=20)
    payment_due_date = models.DateField(blank=True, null=True)
    exported_at = models.DateTimeField(blank=True, null=True)
    payment_status = models.CharField(max_length=20)
    type = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'testapp_invoice'


class TestappInvoiceproduct(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    reduction_rate = models.DecimalField(max_digits=5, decimal_places=2)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'testapp_invoiceproduct'


class TestappItem(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    name = models.CharField(max_length=100)
    description = models.TextField()
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'testapp_item'


class TestappProduct(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    name = models.CharField(max_length=100)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2)
    expense_code = models.CharField(max_length=20)
    is_energy = models.IntegerField()
    fiscal_label = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'testapp_product'


class TestappProfile(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    position = models.CharField(max_length=100)
    date_of_joining = models.DateField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    contact_number = models.CharField(max_length=15)
    user = models.OneToOneField(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'testapp_profile'
