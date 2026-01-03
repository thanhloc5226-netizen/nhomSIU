from django import forms
from .models import (
    Customer,
    Contract,
    TrademarkService,
    CopyrightService,
    BusinessRegistrationService,
    InvestmentService,
    OtherService,
)

# ======================================================
# CUSTOMER FORM
# ======================================================
class CustomerForm(forms.ModelForm):

    # 🔴 BẮT BUỘC EMAIL
    email = forms.EmailField(
        required=True,
        label='Email',
        error_messages={
            'required': 'Vui lòng nhập email',
            'invalid': 'Email không hợp lệ',
        },
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'required': 'required',
        })
    )
    class Meta:
        model = Customer
        fields = [
            'customer_type',
            'status',
            'customer_code',
            'name',
            'address',
            'email',
            'phone',
            'cccd',
            'tax_code',
            'manager',
            'position',
            'note',
        ]

        labels = {
            'customer_type': 'Loại khách hàng',
            'status': 'Trạng thái khách hàng',
            'customer_code': 'Mã khách hàng',
            'name': 'Tên khách hàng',
            'address': 'Địa chỉ',
            'email': 'Email',
            'phone': 'Số điện thoại',
            'cccd': 'Số CCCD',
            'tax_code': 'Mã số thuế',
            'manager': 'Người phụ trách',
            'position': 'Chức danh',
            'note': 'Ghi chú',
        }

        widgets = {
            'customer_type': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'customer_code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'cccd': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_code': forms.TextInput(attrs={'class': 'form-control'}),
            'manager': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    # 🔒 KHÓA LOẠI KHÁCH HÀNG KHI EDIT
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            # Ẩn select loại khách hàng
            self.fields['customer_type'].widget = forms.HiddenInput()

    # 🧠 DỌN DỮ LIỆU THEO LOẠI KHÁCH
    def clean(self):
        cleaned_data = super().clean()
        ctype = cleaned_data.get('customer_type')

        if ctype == 'personal':
            cleaned_data['tax_code'] = None

        if ctype == 'company':
            cleaned_data['cccd'] = None

        return cleaned_data


# ======================================================
# CUSTOMER STATUS FORM (CHỈ ĐỔI TRẠNG THÁI)
# ======================================================
class CustomerStatusForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['status']

        labels = {
            'status': 'Trạng thái khách hàng',
        }

        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

# ======================================================
# CONTRACT FORM  (⚠️ CÓ STATUS – QUAN TRỌNG)
# ======================================================
from django import forms
from .models import Contract

from django import forms
from .models import Contract


class ContractForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = [
            'customer',
            'service_type',
            'contract_no',
            'contract_value',
            'payment_type',
            'prepaid_amount',
        ]

        labels = {
            'customer': 'Khách hàng',
            'service_type': 'Loại dịch vụ',
            'contract_no': 'Số hợp đồng',
            'contract_value': 'Giá trị hợp đồng',
            'payment_type': 'Hình thức thanh toán',
            'prepaid_amount': 'Số tiền trả trước (VNĐ)',
        }

        widgets = {
            'customer': forms.Select(attrs={
                'class': 'form-control select2'
            }),
            'service_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'contract_no': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'VD: HD-001'
            }),
            'contract_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập giá trị hợp đồng',
                'min': 0
            }),
            'payment_type': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_payment_type'
            }),
            'prepaid_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nhập số tiền trả trước',
                'min': 0
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        contract_value = cleaned_data.get('contract_value') or 0
        prepaid_amount = cleaned_data.get('prepaid_amount') or 0

        # 🔐 VALIDATE: tiền trả trước không được âm
        if prepaid_amount < 0:
            raise forms.ValidationError({
                'prepaid_amount': 'Số tiền trả trước không được nhỏ hơn 0'
            })

        # 🔐 VALIDATE: tiền trả trước không được lớn hơn giá trị hợp đồng
        if prepaid_amount > contract_value:
            raise forms.ValidationError({
                'prepaid_amount': 'Số tiền trả trước không được lớn hơn giá trị hợp đồng'
            })

        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Required fields
        self.fields['customer'].required = True
        self.fields['service_type'].required = True
        self.fields['contract_no'].required = True
        self.fields['contract_value'].required = True
        self.fields['payment_type'].required = True

        # prepaid_amount KHÔNG bắt buộc
        self.fields['prepaid_amount'].required = False


# ======================================================
# 1. NHÃN HIỆU
# ======================================================
class TrademarkForm(forms.ModelForm):
    class Meta:
        model = TrademarkService
        exclude = ['contract']

        labels = {
            'applicant': 'Người nộp đơn',
            'address': 'Địa chỉ',
            'email': 'Email',
            'phone': 'Số điện thoại',
            'app_no': 'Số đơn',
            'filing_date': 'Ngày nộp đơn',
            'trademark_image': 'Hình ảnh nhãn hiệu',
            'classification': 'Nhóm sản phẩm/dịch vụ',
            'publish_date': 'Ngày công bố',
            'decision_date': 'Ngày cấp',
            'certificate_file': 'File chứng nhận',
        }

        widgets = {
            'applicant': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'app_no': forms.TextInput(attrs={'class': 'form-control'}),
            'filing_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'classification': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'publish_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'decision_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'trademark_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'certificate_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


# ======================================================
# 2. BẢN QUYỀN
# ======================================================
class CopyrightForm(forms.ModelForm):
    class Meta:
        model = CopyrightService
        exclude = ['contract']

        labels = {
            'work_name': 'Tên tác phẩm',
            'author': 'Tác giả',
            'owner': 'Chủ sở hữu',
            'owner_address': 'Địa chỉ chủ sở hữu',
            'type': 'Loại hình tác phẩm',
            'certificate_no': 'Số chứng nhận',
            'certificate_file': 'File chứng nhận',
        }

        widgets = {
            'work_name': forms.TextInput(attrs={'class': 'form-control'}),
            'author': forms.TextInput(attrs={'class': 'form-control'}),
            'owner': forms.TextInput(attrs={'class': 'form-control'}),
            'owner_address': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.TextInput(attrs={'class': 'form-control'}),
            'certificate_no': forms.TextInput(attrs={'class': 'form-control'}),
            'certificate_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


# ======================================================
# 3. ĐĂNG KÝ KINH DOANH
# ======================================================
class BusinessRegistrationForm(forms.ModelForm):
    class Meta:
        model = BusinessRegistrationService
        exclude = ['contract']

        labels = {
            'company_name': 'Tên công ty',
            'business_type': 'Loại hình kinh doanh',
            'tax_code': 'Mã số thuế',
            'address': 'Địa chỉ',
            'email': 'Email',
            'phone': 'SĐT',
            'legal_representative': 'Người đại diện pháp luật',
            'position': 'Chức danh',
            'charter_capital': 'Vốn điều lệ',
            'certificate_file': 'File chứng nhận',
        }

        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'business_type': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_code': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'legal_representative': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'charter_capital': forms.TextInput(attrs={'class': 'form-control'}),
            'certificate_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


# ======================================================
# 4. ĐĂNG KÝ ĐẦU TƯ
# ======================================================
class InvestmentForm(forms.ModelForm):
    class Meta:
        model = InvestmentService
        exclude = ['contract']

        labels = {
            'project_code': 'Mã dự án',
            'investor': 'Nhà đầu tư',
            'project_name': 'Tên dự án',
            'objective': 'Mục tiêu dự án',
            'address': 'Địa chỉ',
            'total_capital': 'Tổng vốn',
            'certificate_file': 'File chứng nhận',
        }

        widgets = {
            'project_code': forms.TextInput(attrs={'class': 'form-control'}),
            'investor': forms.TextInput(attrs={'class': 'form-control'}),
            'project_name': forms.TextInput(attrs={'class': 'form-control'}),
            'objective': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'total_capital': forms.TextInput(attrs={'class': 'form-control'}),
            'certificate_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


# ======================================================
# 5. DỊCH VỤ KHÁC
# ======================================================
class OtherServiceForm(forms.ModelForm):
    class Meta:
        model = OtherService
        exclude = ['contract']

        labels = {
            'description': 'Mô tả dịch vụ',
            'legal_representative': 'Người đại diện',
            'position': 'Chức danh',
            'phone': 'Số điện thoại',
            'email': 'Email',
            'certificate_file': 'File đính kèm',
        }

        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'legal_representative': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Chỉ nhập số'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'certificate_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
from .models import PaymentInstallment


class PaymentInstallmentForm(forms.ModelForm):
    class Meta:
        model = PaymentInstallment
        fields = ['is_paid', 'paid_date']

        labels = {
            'is_paid': 'Đã thanh toán',
            'paid_date': 'Ngày thanh toán',
        }

        widgets = {
            'is_paid': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            # Sửa lại thành datetime-local hoặc date để người dùng tự chọn
            'paid_date': forms.DateInput(attrs={
                'type': 'date', # Hoặc 'datetime-local' nếu muốn có cả giờ
                'class': 'form-control'
            }),
        }
from django.forms import modelformset_factory

TrademarkFormSet = modelformset_factory(
    TrademarkService,
    form=TrademarkForm,
    extra=0,
    can_delete=True
)

CopyrightFormSet = modelformset_factory(
    CopyrightService,
    form=CopyrightForm,
    extra=0,
    can_delete=True
)

