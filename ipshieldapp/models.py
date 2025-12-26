from django.db import models
from django.core.validators import RegexValidator
# ============================
# KHÁCH HÀNG
# ============================
from django.db import models
from django.db import models
from django.core.validators import RegexValidator

# ============================
# VALIDATORS (THÔNG BÁO TV)
# ============================
phone_validator = RegexValidator(
    regex=r'^\d+$',
    message='Số điện thoại chỉ được nhập chữ số'
)

number_validator = RegexValidator(
    regex=r'^\d+$',
    message='Trường này chỉ được nhập số'
)

# ============================
# KHÁCH HÀNG
# ============================
class Customer(models.Model):

    CUSTOMER_TYPE_CHOICES = (
        ('personal', 'Cá nhân'),
        ('company', 'Doanh nghiệp'),
    )

    CUSTOMER_STATUS_CHOICES = (
        ('approved', 'Chờ duyệt'),
        ('pending', 'Đang xử lý'),
        ('completed', 'Hoàn tất'),
    )

    customer_type = models.CharField(
        max_length=20,
        choices=CUSTOMER_TYPE_CHOICES,
        default='personal',
        verbose_name='Loại khách hàng'
    )

    status = models.CharField(
        max_length=20,
        choices=CUSTOMER_STATUS_CHOICES,
        default='approved',
        verbose_name='Trạng thái'
    )

    customer_code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Mã khách hàng'
    )

    name = models.CharField(
        max_length=255,
        verbose_name='Tên khách hàng'
    )

    address = models.CharField(
        max_length=255,
        verbose_name='Địa chỉ'
    )

    phone = models.CharField(
        max_length=20,
        validators=[phone_validator],
        verbose_name='Số điện thoại'
    )

    email = models.EmailField(
        verbose_name='Email'
    )

    cccd = models.CharField(
        max_length=20,
        validators=[number_validator],
        blank=True,
        null=True,
        verbose_name='Số CCCD'
    )

    tax_code = models.CharField(
        max_length=20,
        validators=[number_validator],
        blank=True,
        null=True,
        verbose_name='Mã số thuế'
    )

    manager = models.CharField(
        max_length=255,
        verbose_name='Người phụ trách'
    )

    position = models.CharField(
        max_length=100,
        verbose_name='Chức danh'
    )

    note = models.TextField(
        blank=True,
        null=True,
        verbose_name='Ghi chú'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )

    class Meta:
        verbose_name = 'Khách hàng'
        verbose_name_plural = 'Khách hàng'

    def __str__(self):
        return f"{self.customer_code} - {self.name}"

# ============================
# HỢP ĐỒNG
# ============================
class Contract(models.Model):

    SERVICE_TYPE_CHOICES = (
        ('nhanhieu', 'Đăng ký nhãn hiệu'),
        ('banquyen', 'Bản quyền tác giả'),
        ('dkkd', 'Đăng ký kinh doanh'),
        ('dautu', 'Đăng ký đầu tư'),
        ('khac', 'Dịch vụ khác'),
    )

    CONTRACT_STATUS_CHOICES = (
        ('pending', 'Đang chờ xử lý'),
        ('processing', 'Đang xử lý'),
        ('completed', 'Hoàn thành'),
        ('paused', 'Ngưng'),
    )
    PAYMENT_TYPE_CHOICES = (
        ('full', 'Trả dứt điểm'),
        ('installment', 'Trả góp'),
    )

    INSTALLMENT_COUNT_CHOICES = (
        (3, '3 đợt'),
        (6, '6 đợt'),
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='contracts'
    )

    service_type = models.CharField(
        max_length=50,
        choices=SERVICE_TYPE_CHOICES
    )

    contract_no = models.CharField(max_length=50, unique=True)
    # 🟢 GIÁ TRỊ HỢP ĐỒNG
    contract_value = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        verbose_name='Giá trị hợp đồng'
    )

    # 🟢 TRẢ ĐỨT / TRẢ GÓP
    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES,
        verbose_name='Hình thức thanh toán'
    )

    # 🟢 CHỈ DÙNG KHI TRẢ GÓP
    installment_count = models.PositiveSmallIntegerField(
        choices=INSTALLMENT_COUNT_CHOICES,
        null=True,
        blank=True,
        verbose_name='Số đợt thanh toán'
    )
    status = models.CharField(
        max_length=20,
        choices=CONTRACT_STATUS_CHOICES,
        default='pending'
    )

    @property
    def paid_installments(self):
        return self.installments.filter(is_paid=True).count()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.contract_no
# thanh toán hợp đồng
class PaymentInstallment(models.Model):
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='installments'
    )

    installment_no = models.PositiveSmallIntegerField(
        verbose_name='Đợt'
    )

    amount = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        verbose_name='Số tiền'
    )

    is_paid = models.BooleanField(
        default=False,
        verbose_name='Đã thanh toán'
    )

    paid_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Ngày thanh toán'
    )

    class Meta:
        verbose_name = 'Đợt thanh toán'
        verbose_name_plural = 'Các đợt thanh toán'
        unique_together = ('contract', 'installment_no')

    def __str__(self):
        return f"{self.contract.contract_no} - Đợt {self.installment_no}"

# ============================
# 1. NHÃN HIỆU
# ============================
class TrademarkService(models.Model):
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='trademarks'
    )

    applicant = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(
        max_length=20,
        validators=[phone_validator],
        verbose_name='Số điện thoại'
    )

    app_no = models.CharField(max_length=50)
    filing_date = models.DateField()
    trademark_name = models.CharField(max_length=255)
    trademark_image = models.ImageField(
        upload_to='images/trademark/',
        blank=True,
        null=True
    )

    classification = models.TextField()
    publish_date = models.DateField(blank=True, null=True)
    decision_date = models.DateField(blank=True, null=True)

    certificate_file = models.FileField(
        upload_to='images/certificates/',
        blank=True,
        null=True
    )


# ============================
# 2. BẢN QUYỀN
# ============================
class CopyrightService(models.Model):
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='copyrights'
    )

    work_name = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    owner = models.CharField(max_length=255)
    owner_address = models.CharField(max_length=255)

    type = models.CharField(max_length=255)
    certificate_no = models.CharField(max_length=50)

    certificate_file = models.FileField(
        upload_to='images/certificates/',
        blank=True,
        null=True
    )


# ============================
# 3. ĐĂNG KÝ KINH DOANH
# ============================
class BusinessRegistrationService(models.Model):
    contract = models.OneToOneField(
        Contract,
        on_delete=models.CASCADE,
        related_name='business'
    )

    company_name = models.CharField(max_length=255)
    business_type = models.CharField(max_length=100)

    tax_code = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255)

    email = models.EmailField()
    phone = models.CharField(
        max_length=20,
        validators=[phone_validator],
        verbose_name='Số điện thoại'
    )

    legal_representative = models.CharField(max_length=255)
    position = models.CharField(max_length=100)

    charter_capital = models.CharField(max_length=100)

    certificate_file = models.FileField(
        upload_to='images/certificates/',
        blank=True,
        null=True
    )


# ============================
# 4. ĐĂNG KÝ ĐẦU TƯ
# ============================
class InvestmentService(models.Model):
    contract = models.OneToOneField(
        Contract,
        on_delete=models.CASCADE,
        related_name='investment'
    )

    project_code = models.CharField(max_length=100)
    investor = models.CharField(max_length=255)

    project_name = models.CharField(max_length=255)
    objective = models.TextField()

    address = models.CharField(max_length=255)
    total_capital = models.CharField(max_length=100)

    certificate_file = models.FileField(
        upload_to='images/certificates/',
        blank=True,
        null=True
    )


# ============================
# 5. DỊCH VỤ KHÁC
# ============================
class OtherService(models.Model):
    contract = models.OneToOneField(
        Contract,
        on_delete=models.CASCADE,
        related_name='other_service'
    )

    description = models.TextField()
    legal_representative = models.CharField(max_length=255,null=False)
    position = models.CharField(max_length=100)
    phone = models.CharField(
        max_length=20,
        validators=[phone_validator],
        verbose_name='Số điện thoại'
    )
    email = models.EmailField()
    certificate_file = models.FileField(
        upload_to='images/certificates/',
        blank=True,
        null=True
    )


# ============================
# LỊCH SỬ HỢP ĐỒNG
# ============================
class ContractHistory(models.Model):
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='histories'
    )

    user = models.CharField(max_length=255)
    action = models.CharField(max_length=255)

    old_data = models.TextField(blank=True, null=True)
    new_data = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.contract.contract_no} - {self.action}"
# ============================
# carousel
# ============================
class Slider(models.Model):
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to='sliders/')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title
# ============================
# MASCOT
# ============================
class Mascot(models.Model):
    title = models.CharField(max_length=100)
    speech = models.CharField(max_length=255, default="Xin chào! Tôi là Toki!")
    image = models.ImageField(upload_to='mascots/')
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title