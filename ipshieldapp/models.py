from django.db import models
from django.core.validators import RegexValidator
from django.db.models import Sum
# ============================
# KHÁCH HÀNG
# ============================

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
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

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
        ('installment', 'Trả nhiều đợt'),
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

    # 🟢 TRẢ ĐỨT ĐIỂM / TRẢ NHIỀU ĐỢT
    payment_type = models.CharField(
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES,
        verbose_name='Hình thức thanh toán'
    )

    # 🟢 SỐ TIỀN TRẢ TRƯỚC
    prepaid_amount = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        verbose_name='Số tiền trả trước'
    )
    
    
    status = models.CharField(
        max_length=20,
        choices=CONTRACT_STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(default=timezone.now)


    class Meta:
        verbose_name = 'Hợp đồng'
        verbose_name_plural = 'Hợp đồng'
        indexes = [
            models.Index(fields=['contract_no']),
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['created_at']),
        ]

    def clean(self):
        super().clean()
        
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def total_paid(self):
        from django.db.models import Sum
        return self.installments.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0

    @property
    def remaining_amount(self):
        return self.contract_value - self.total_paid

    @property
    def payment_progress(self):
        """%x tiến độ thanh toán"""
        if self.contract_value == 0:
            return 0
        return round((self.total_paid / self.contract_value) * 100, 2)

    @property
    def is_fully_paid(self):
        """Đã thanh toán đủ chưa"""
        return self.total_paid >= self.contract_value


    def __str__(self):
        return f"{self.contract_no} - {self.get_service_type_display()}"


class PaymentInstallment(models.Model):
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='installments'
    )

    # TỔNG TRẢ GÓP
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Số tiền đợt thanh toán'
    )

    # TIỀN TRẢ TRƯỚC
    paid_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name='Số tiền đã trả'
    )

    due_date = models.DateField(null=True, blank=True)
    is_paid = models.BooleanField(default=False, verbose_name='Đã thanh toán')
    paid_date = models.DateField(null=True, blank=True)

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        verbose_name = 'Đợt thanh toán'
        verbose_name_plural = 'Các đợt thanh toán'
        # unique_together = ('contract')
        ordering = ['contract']
        indexes = [
            models.Index(fields=['contract', 'is_paid']),
            models.Index(fields=['paid_date']),
            models.Index(fields=['due_date']),
        ]

    def clean(self):
        super().clean()

        if self.amount <= 0:
            raise ValidationError({'amount': 'Số tiền đợt phải > 0'})

        if self.paid_amount < 0:
            raise ValidationError({'paid_amount': 'Số tiền đã trả không hợp lệ'})

        if self.paid_amount > self.amount:
            raise ValidationError({'paid_amount': 'Số tiền trả vượt quá số tiền đợt'})




    def save(self, *args, **kwargs):
        if self.paid_amount >= self.amount:
            self.is_paid = True
            if not self.paid_date:
                self.paid_date = timezone.now().date()
        else:
            self.is_paid = False
            self.paid_date = None

        super().save(*args, **kwargs)

    
    def add_payment(self, amount, paid_date=None, notes=''):
        if amount <= 0:
            raise ValidationError('Số tiền phải lớn hơn 0')

        self.paid_amount += amount

        if self.paid_amount >= self.amount:
            self.is_paid = True
            self.paid_date = paid_date or timezone.now().date()

        if notes:
            self.notes = notes

        self.save()

    

    
    def __str__(self):
        status = "✓" if self.is_paid else "✗"
        return f"{self.contract.contract_no} - Đợt  ({status})"
    
    @property
    def remaining_amount(self):
        return max(self.amount - self.paid_amount, 0)
    
class PaymentLog(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='payment_logs')
    installment = models.ForeignKey(PaymentInstallment, on_delete=models.CASCADE, related_name='logs')
    amount_paid = models.DecimalField(max_digits=15, decimal_places=0)
    paid_at = models.DateTimeField(verbose_name="Thời gian thanh toán")
    is_exported_bill = models.BooleanField(default=False)
    bill_exported_at = models.DateTimeField(null=True, blank=True)
    def __str__(self):
        return f"Thanh toán {self.amount_paid} cho HĐ {self.contract.id}"

    class Meta:
        ordering = ['-paid_at'] # Cái mới nhất hiện lên đầu

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
# ============================
#Nhãn hiệu độc quyền
# ============================
class NhanHieuDocQuyen(models.Model):
    name = models.CharField("Tên nhãn hiệu", max_length=100, blank=True)
    image = models.ImageField("Ảnh nhãn hiệu", upload_to="logokhachhang/logobrand/")
    is_active = models.BooleanField("Hiển thị", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Nhãn hiệu độc quyền"
        verbose_name_plural = "Nhãn hiệu độc quyền"

    def __str__(self):
        return self.name or f"Nhãn hiệu {self.id}"
