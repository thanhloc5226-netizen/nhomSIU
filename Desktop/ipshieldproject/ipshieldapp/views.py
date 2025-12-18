# ===============================================
# IMPORTS
# ===============================================
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from django.http import FileResponse, Http404
from django.db import IntegrityError
import os
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from .models import *
from .forms import *

def lock_payment_fields(contract_form):
    contract_form.fields['payment_type'].disabled = True
    contract_form.fields['installment_count'].disabled = True
    contract_form.fields['contract_value'].disabled = True

# ===============================================
# CUSTOMER LIST + SEARCH
# ===============================================
def home(request):
    q = request.GET.get('q', '').strip()
    customers = Customer.objects.all()

    if q:
        customers = customers.filter(
            Q(customer_code__icontains=q) |
            Q(name__icontains=q) |
            Q(email__icontains=q) |
            Q(phone__icontains=q)
        )

    sliders = Slider.objects.filter(is_active=True)

    mascots = Mascot.objects.filter(is_active=True)

    return render(request, 'khachhang.html', {
        'customers': customers,
        'sliders': sliders,
        'mascots': mascots,
    })


# ===============================================
# CUSTOMER CREATE (ĐÃ SỬA - XỬ LÝ TRÙNG MÃ)
# ===============================================
def add_contract(request):
    if request.method == 'POST':
        contract_form = ContractForm(request.POST, request.FILES)

        if contract_form.is_valid():
            try:
                # ⛔ CHƯA SAVE
                contract = contract_form.save(commit=False)

                # ==========================
                # XỬ LÝ THANH TOÁN
                # ==========================
                if contract.payment_type == 'full':
                    contract.status = 'completed'
                else:
                    contract.status = 'processing'

                contract.save()

                # ==========================
                # TẠO CÁC ĐỢT THANH TOÁN
                # ==========================
                if contract.payment_type == 'installment':
                    amount = contract.contract_value / contract.installment_count
                    for i in range(1, contract.installment_count + 1):
                        PaymentInstallment.objects.create(
                            contract=contract,
                            installment_no=i,
                            amount=amount
                        )

                # ==========================
                # CẬP NHẬT TRẠNG THÁI KHÁCH
                # ==========================
                customer = contract.customer
                customer.status = 'pending'
                customer.save()

                # CHỌN FORM DỊCH VỤ
                if contract.service_type == 'nhanhieu':
                    service_form = TrademarkForm(request.POST, request.FILES)
                elif contract.service_type == 'banquyen':
                    service_form = CopyrightForm(request.POST, request.FILES)
                elif contract.service_type == 'dkkd':
                    service_form = BusinessRegistrationForm(request.POST, request.FILES)
                elif contract.service_type == 'dautu':
                    service_form = InvestmentForm(request.POST, request.FILES)
                else:
                    service_form = OtherServiceForm(request.POST, request.FILES)

                if service_form.is_valid():
                    service = service_form.save(commit=False)
                    service.contract = contract
                    service.save()

                    messages.success(request, "✅ Tạo hợp đồng thành công!")
                    return redirect('home')
                else:
                    contract.delete()
                    messages.error(request, "❌ Dữ liệu dịch vụ không hợp lệ.")
                    for errors in service_form.errors.values():
                        for error in errors:
                            messages.error(request, error)

            except IntegrityError:
                messages.error(request, "⚠️ Số hợp đồng đã tồn tại!")
        else:
            for errors in contract_form.errors.values():
                for error in errors:
                    messages.error(request, error)

    else:
        contract_form = ContractForm()



    return render(request, "add_contract.html", {
        'contract_form': contract_form,
        'trademark_form': TrademarkForm(),
        'copyright_form': CopyrightForm(),
        'business_form': BusinessRegistrationForm(),
        'investment_form': InvestmentForm(),
        'other_form': OtherServiceForm(),
       \
    })



# ===============================================
# CUSTOMER DETAIL
# ===============================================
def customer_detail(request, id):
    customer = get_object_or_404(Customer, id=id)
    contracts = customer.contracts.all()

    return render(request, 'customer_detail.html', {
        'customer': customer,
        'contracts': contracts
    })


# ===============================================
# CUSTOMER CHANGE STATUS
# (❗ KHÓA SỬA TAY KHI ĐÃ CÓ HỢP ĐỒNG)
# ===============================================
def customer_change_status(request, pk):
    customer = get_object_or_404(Customer, pk=pk)

    if request.method == 'POST':
        form = CustomerStatusForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Cập nhật trạng thái thành công!")
            return redirect('customer_detail', id=customer.id)
    else:
        form = CustomerStatusForm(instance=customer)

    return render(request, 'customer_change_status.html', {
        'customer': customer,
        'form': form
    })



# ===============================================
# CUSTOMER EDIT (ĐÃ SỬA - XỬ LÝ TRÙNG MÃ)
# ===============================================
def customer_edit(request, id):
    customer = get_object_or_404(Customer, id=id)

    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "✅ Cập nhật khách hàng thành công!")
                return redirect('customer_detail', id=id)
            except IntegrityError as e:
                customer_code = form.cleaned_data.get('customer_code', '')
                messages.error(request, f"⚠️ Mã khách hàng '{customer_code}' đã tồn tại! Vui lòng nhập mã khác.")
            except Exception as e:
                messages.error(request, f"❌ Có lỗi xảy ra: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request,
                                   f"{form.fields.get(field).label if field in form.fields else field}: {error}")
    else:
        form = CustomerForm(instance=customer)

    return render(request, 'customer_edit.html', {
        'form': form,
        'customer': customer
    })


# ===============================================
# CUSTOMER DELETE
# ===============================================
def customer_delete(request, id):
    customer = get_object_or_404(Customer, id=id)

    if request.method == "POST":
        customer.delete()
        messages.success(request, "✅ Đã xóa khách hàng!")
        return redirect('home')

    return render(request, 'customer_delete_confirm.html', {
        'customer': customer
    })



# ===============================================
# CONTRACT LIST
# ===============================================
def contract_list(request):
    contracts = Contract.objects.select_related("customer").order_by("-created_at")
    return render(request, "contract_list.html", {"contracts": contracts})


# ===============================================
# CONTRACT DETAIL
# ===============================================
from datetime import date
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

def contract_detail(request, id):
    contract = get_object_or_404(Contract, id=id)
    installments = contract.installments.all().order_by('installment_no')

    # ✅ ĐẾM SỐ ĐỢT ĐÃ TRẢ
    paid_count = installments.filter(is_paid=True).count()

    # ==========================
    # LẤY DỊCH VỤ
    # ==========================
    if contract.service_type == "nhanhieu":
        service = TrademarkService.objects.get(contract=contract)
    elif contract.service_type == "banquyen":
        service = CopyrightService.objects.get(contract=contract)
    elif contract.service_type == "dkkd":
        service = BusinessRegistrationService.objects.get(contract=contract)
    elif contract.service_type == "dautu":
        service = InvestmentService.objects.get(contract=contract)
    else:
        service = OtherService.objects.get(contract=contract)

    # ==========================
    # 🔥 AUTO HOÀN THÀNH – TRẢ ĐỨT
    # ==========================
    if contract.payment_type == "full" and contract.status != "completed":
        contract.status = "completed"
        contract.save(update_fields=["status"])

    # ==========================
    # 🔥 CẬP NHẬT THANH TOÁN – TRẢ GÓP
    # ==========================
    if request.method == "POST" and contract.payment_type == "installment":

        for ins in installments:
            checkbox_name = f"paid_{ins.id}"

            if checkbox_name in request.POST and not ins.is_paid:
                ins.is_paid = True
                ins.paid_date = date.today()
                ins.save()

        # 👉 nếu trả đủ → hoàn thành
        if not installments.filter(is_paid=False).exists():
            contract.status = "completed"
            contract.save(update_fields=["status"])

        messages.success(request, "✅ Cập nhật thanh toán thành công")
        return redirect("contract_detail", id=contract.id)

    return render(request, "contract_detail.html", {
        "contract": contract,
        "service": service,
        "installments": installments,
        "paid_count": paid_count,  # 🔥 DÒNG QUYẾT ĐỊNH
    })




# ===============================================
# CONTRACT EDIT (ĐÃ SỬA - CẬP NHẬT TRẠNG THÁI)
# ===============================================
def contract_edit(request, id):
    contract = get_object_or_404(Contract, id=id)

    # ==========================
    # LẤY FORM DỊCH VỤ
    # ==========================
    if contract.service_type == "nhanhieu":
        service = TrademarkService.objects.get(contract=contract)
        ServiceForm = TrademarkForm
    elif contract.service_type == "banquyen":
        service = CopyrightService.objects.get(contract=contract)
        ServiceForm = CopyrightForm
    elif contract.service_type == "dkkd":
        service = BusinessRegistrationService.objects.get(contract=contract)
        ServiceForm = BusinessRegistrationForm
    elif contract.service_type == "dautu":
        service = InvestmentService.objects.get(contract=contract)
        ServiceForm = InvestmentForm
    else:
        service = OtherService.objects.get(contract=contract)
        ServiceForm = OtherServiceForm

    # ==========================
    # POST
    # ==========================
    if request.method == "POST":
        contract_form = ContractForm(request.POST, instance=contract)
        service_form = ServiceForm(request.POST, request.FILES, instance=service)

        lock_payment_fields(contract_form)

        if contract_form.is_valid() and service_form.is_valid():
            try:
                # ⛔ KHÔNG save thẳng
                contract_obj = contract_form.save(commit=False)

                # 🔒 GIỮ NGUYÊN THANH TOÁN
                contract_obj.payment_type = contract.payment_type
                contract_obj.installment_count = contract.installment_count
                contract_obj.contract_value = contract.contract_value

                contract_obj.save()
                service_form.save()

                # ==========================
                # CẬP NHẬT TRẠNG THÁI KHÁCH
                # ==========================
                customer = contract_obj.customer
                if customer.contracts.filter(
                    status__in=['pending', 'processing']
                ).exists():
                    customer.status = 'pending'
                else:
                    customer.status = 'pending'
                customer.save()

                ContractHistory.objects.create(
                    contract=contract_obj,
                    user="Admin",
                    action="Cập nhật hợp đồng",
                    new_data=str(request.POST)
                )

                messages.success(request, "✅ Cập nhật hợp đồng thành công!")
                return redirect("contract_detail", id=id)

            except IntegrityError:
                messages.error(request, "⚠️ Số hợp đồng đã tồn tại!")
            except Exception as e:
                messages.error(request, f"❌ Có lỗi xảy ra: {str(e)}")

    # ==========================
    # GET
    # ==========================
    else:
        contract_form = ContractForm(instance=contract)
        service_form = ServiceForm(instance=service)
        lock_payment_fields(contract_form)

    return render(request, "contract_edit.html", {
        "contract_form": contract_form,
        "service_form": service_form,
        "contract": contract,
    })


# ===============================================
# DOWNLOAD CERTIFICATE
# ===============================================
def download_certificate(request, id):
    contract = get_object_or_404(Contract, id=id)

    if contract.service_type == "nhanhieu":
        service = TrademarkService.objects.get(contract=contract)
    elif contract.service_type == "banquyen":
        service = CopyrightService.objects.get(contract=contract)
    elif contract.service_type == "dkkd":
        service = BusinessRegistrationService.objects.get(contract=contract)
    elif contract.service_type == "dautu":
        service = InvestmentService.objects.get(contract=contract)
    else:
        service = OtherService.objects.get(contract=contract)

    if not service.certificate_file:
        raise Http404("Không có giấy chứng nhận")

    return FileResponse(
        service.certificate_file.open("rb"),
        as_attachment=True,
        filename=os.path.basename(service.certificate_file.name)
    )
# ===============================================
# CUSTOMER CREATE
# ===============================================
def add_customer(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "✅ Thêm khách hàng thành công!")
                return redirect('home')
            except IntegrityError:
                messages.error(request, "⚠️ Mã khách hàng đã tồn tại!")
        else:
            for errors in form.errors.values():
                for error in errors:
                    messages.error(request, error)
    else:
        form = CustomerForm()

    return render(request, 'add_customer.html', {'form': form})


from django.http import JsonResponse
from django.db.models import Q

from django.http import JsonResponse
from django.db.models import Q


def search_customer(request):
    """
    API tìm kiếm khách hàng theo mã hoặc tên
    URL: /api/search-customer/?q=ma123
    """
    query = request.GET.get('q', '').strip()

    # Yêu cầu ít nhất 1 ký tự để test
    if len(query) < 1:
        return JsonResponse([], safe=False)

    try:
        # Tìm kiếm theo customer_code hoặc name
        customers = Customer.objects.filter(
            Q(customer_code__icontains=query) |
            Q(name__icontains=query)
        )[:10]

        # Tạo danh sách kết quả
        results = []
        for c in customers:
            results.append({
                'id': c.id,
                'code': c.customer_code,
                'name': c.name,
                'phone': str(c.phone) if c.phone else '',
                'email': c.email if c.email else ''
            })

        return JsonResponse(results, safe=False)

    except Exception as e:
        import traceback
        print(f"Error: {str(e)}")
        print(traceback.format_exc())

        return JsonResponse({
            'error': str(e)
        }, status=500)
# ===============================================
# LOGIN / LOGOUT
# ===============================================
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Sai tên đăng nhập hoặc mật khẩu")

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')
# ===============================================
# REQUIRE LOGIN FOR ALL VIEWS
# ===============================================
def protect_views(*views):
    for view in views:
        globals()[view.__name__] = login_required(view)


protect_views(
    home,
    add_contract,
    customer_detail,
    customer_change_status,
    customer_edit,
    customer_delete,
    contract_list,
    contract_detail,
    contract_edit,
    download_certificate,
    add_customer,
    search_customer,
)


