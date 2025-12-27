# ===============================================
# IMPORTS
# ===============================================
from decimal import Decimal
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

def lock_contract_fields(contract_form):

    for field_name, field in contract_form.fields.items():
        field.disabled = True
        field.widget.attrs['readonly'] = True
        field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' readonly-field'

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
        print("\n" + "=" * 60)
        print("🔍 POST REQUEST RECEIVED")
        print("=" * 60)

        # Debug: Print all POST data
        print("\n📋 POST Data Keys:")
        for key in request.POST.keys():
            if 'trademark' in key or 'copyright' in key:
                print(f"  {key}: {request.POST.get(key)}")

        # ===== VALIDATE CONTRACT FORM =====
        contract_form = ContractForm(request.POST, request.FILES)

        if not contract_form.is_valid():
            print("\n❌ Contract form invalid:")
            print(contract_form.errors)
            for field, errors in contract_form.errors.items():
                for error in errors:
                    field_label = contract_form.fields.get(field).label if field in contract_form.fields else field
                    messages.error(request, f"{field_label}: {error}")

            return render(request, "add_contract.html", {
                'contract_form': contract_form,
                'trademark_formset': TrademarkFormSet(request.POST, request.FILES, prefix='trademark'),
                'copyright_formset': CopyrightFormSet(request.POST, request.FILES, prefix='copyright'),
                'business_form': BusinessRegistrationForm(request.POST, request.FILES),
                'investment_form': InvestmentForm(request.POST, request.FILES),
                'other_form': OtherServiceForm(request.POST, request.FILES),
            })

        print("✅ Contract form valid")

        # ===== SAVE CONTRACT =====
        contract = contract_form.save(commit=False)
        contract.status = 'completed' if contract.payment_type == 'full' else 'processing'

        try:
            contract.save()
            print(f"✅ Contract saved: {contract.contract_no}")

            # ===== HANDLE SERVICE BASED ON TYPE =====
            service_type = contract.service_type
            print(f"\n📦 Processing service type: {service_type}")

            # ==================================================
            #           🔥 NHÃN HIỆU (TRADEMARK)
            # ==================================================
            if service_type == 'nhanhieu':
                print("\n🏷️ Processing TRADEMARK formset...")

                trademark_formset = TrademarkFormSet(
                    request.POST,
                    request.FILES,
                    prefix='trademark'
                )

                print(f"   Management form - TOTAL_FORMS: {request.POST.get('trademark-TOTAL_FORMS')}")
                print(f"   Management form - INITIAL_FORMS: {request.POST.get('trademark-INITIAL_FORMS')}")

                if not trademark_formset.is_valid():
                    print("❌ Trademark formset invalid:")
                    print(f"   Errors: {trademark_formset.errors}")
                    print(f"   Non-form errors: {trademark_formset.non_form_errors()}")

                    contract.delete()
                    
                    # Show formset errors properly
                    for idx, form_errors in enumerate(trademark_formset.errors):
                        if form_errors:
                            for field, errors in form_errors.items():
                                for error in errors:
                                    messages.error(request, f"Nhãn hiệu #{idx + 1} - {field}: {error}")

                    # Show non-form errors
                    for error in trademark_formset.non_form_errors():
                        messages.error(request, f"Lỗi formset: {error}")

                    # 🔴 QUAN TRỌNG: Return với context đầy đủ
                    return render(request, "add_contract.html", {
                        'contract_form': contract_form,
                        'trademark_formset': trademark_formset,  # Giữ nguyên formset để hiển thị lỗi
                        'copyright_formset': CopyrightFormSet(prefix='copyright', queryset=CopyrightService.objects.none()),
                        'business_form': BusinessRegistrationForm(),
                        'investment_form': InvestmentForm(),
                        'other_form': OtherServiceForm(),
                    })

                print("✅ Trademark formset valid")

                # Count valid forms BEFORE saving
                valid_forms = [
                    form for form in trademark_formset 
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False)
                ]
                
                if len(valid_forms) == 0:
                    contract.delete()
                    messages.error(request, "⚠️ Vui lòng thêm ít nhất 1 nhãn hiệu!")
                    
                    # Return với formset để giữ nguyên dữ liệu đã nhập
                    return render(request, "add_contract.html", {
                        'contract_form': contract_form,
                        'trademark_formset': trademark_formset,
                        'copyright_formset': CopyrightFormSet(prefix='copyright', queryset=CopyrightService.objects.none()),
                        'business_form': BusinessRegistrationForm(),
                        'investment_form': InvestmentForm(),
                        'other_form': OtherServiceForm(),
                    })
                
                # Save valid forms
                saved_count = 0
                for idx, form in enumerate(valid_forms):
                    print(f"   Form {idx}: {form.cleaned_data.get('trademark_name', 'N/A')}")
                    
                    instance = form.save(commit=False)
                    instance.contract = contract
                    instance.save()
                    saved_count += 1
                    print(f"   ✅ Saved trademark #{saved_count}")

                print(f"✅ Saved {saved_count} trademarks")

                # Get valid forms (not marked for deletion, has data)
                saved_count = 0
                for idx, form in enumerate(trademark_formset):
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                        print(f"   Form {idx}: {form.cleaned_data.get('trademark_name', 'N/A')}")

                        # Save instance
                        instance = form.save(commit=False)
                        instance.contract = contract
                        instance.save()
                        saved_count += 1
                        print(f"   ✅ Saved trademark #{saved_count}")

                if saved_count == 0:
                    contract.delete()
                    messages.error(request, "⚠️ Vui lòng thêm ít nhất 1 nhãn hiệu!")
                    return redirect('add_contract')

                print(f"✅ Saved {saved_count} trademarks")

            # ==================================================
            # 🔥 BẢN QUYỀN (COPYRIGHT)
            # ==================================================
            elif service_type == 'banquyen':
                print("\n©️ Processing COPYRIGHT formset...")

                copyright_formset = CopyrightFormSet(
                    request.POST,
                    request.FILES,
                    prefix='copyright'
                )

                print(f"   Management form - TOTAL_FORMS: {request.POST.get('copyright-TOTAL_FORMS')}")
                print(f"   Management form - INITIAL_FORMS: {request.POST.get('copyright-INITIAL_FORMS')}")

                if not copyright_formset.is_valid():
                    print("❌ Copyright formset invalid:")
                    print(f"   Errors: {copyright_formset.errors}")
                    print(f"   Non-form errors: {copyright_formset.non_form_errors()}")

                    contract.delete()
                    
                    for idx, form_errors in enumerate(copyright_formset.errors):
                        if form_errors:
                            for field, errors in form_errors.items():
                                for error in errors:
                                    messages.error(request, f"Bản quyền #{idx + 1} - {field}: {error}")

                    for error in copyright_formset.non_form_errors():
                        messages.error(request, f"Lỗi formset: {error}")

                    # 🔴 Return với context đầy đủ
                    return render(request, "add_contract.html", {
                        'contract_form': contract_form,
                        'trademark_formset': TrademarkFormSet(prefix='trademark', queryset=TrademarkService.objects.none()),
                        'copyright_formset': copyright_formset,  # Giữ nguyên formset
                        'business_form': BusinessRegistrationForm(),
                        'investment_form': InvestmentForm(),
                        'other_form': OtherServiceForm(),
                    })

                print("✅ Copyright formset valid")

                # Count valid forms BEFORE saving
                valid_forms = [
                    form for form in copyright_formset 
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False)
                ]
                
                if len(valid_forms) == 0:
                    contract.delete()
                    messages.error(request, "⚠️ Vui lòng thêm ít nhất 1 bản quyền!")
                    
                    return render(request, "add_contract.html", {
                        'contract_form': contract_form,
                        'trademark_formset': TrademarkFormSet(prefix='trademark', queryset=TrademarkService.objects.none()),
                        'copyright_formset': copyright_formset,
                        'business_form': BusinessRegistrationForm(),
                        'investment_form': InvestmentForm(),
                        'other_form': OtherServiceForm(),
                    })

                # Save valid forms
                saved_count = 0
                for idx, form in enumerate(valid_forms):
                    print(f"   Form {idx}: {form.cleaned_data.get('work_name', 'N/A')}")

                    instance = form.save(commit=False)
                    instance.contract = contract
                    instance.save()
                    saved_count += 1
                    print(f"   ✅ Saved copyright #{saved_count}")

                print(f"✅ Saved {saved_count} copyrights")

            # ==================================================
            # OTHER SERVICES (DKKD, DAUTU, KHAC)
            # ==================================================
            elif service_type == 'dkkd':
                form = BusinessRegistrationForm(request.POST, request.FILES)
                if not form.is_valid():
                    contract.delete()
                    for field, errors in form.errors.items():
                        for error in errors:
                            field_label = form.fields.get(field).label if field in form.fields else field
                            messages.error(request, f"ĐKKD - {field_label}: {error}")
                    
                    # 🔴 Return với context đầy đủ
                    return render(request, "add_contract.html", {
                        'contract_form': contract_form,
                        'trademark_formset': TrademarkFormSet(prefix='trademark', queryset=TrademarkService.objects.none()),
                        'copyright_formset': CopyrightFormSet(prefix='copyright', queryset=CopyrightService.objects.none()),
                        'business_form': form,  # Giữ form để hiển thị lỗi
                        'investment_form': InvestmentForm(),
                        'other_form': OtherServiceForm(),
                    })

                obj = form.save(commit=False)
                obj.contract = contract
                obj.save()
                print("✅ Saved business registration")

            elif service_type == 'dautu':
                form = InvestmentForm(request.POST, request.FILES)
                if not form.is_valid():
                    contract.delete()
                    for field, errors in form.errors.items():
                        for error in errors:
                            field_label = form.fields.get(field).label if field in form.fields else field
                            messages.error(request, f"Đầu tư - {field_label}: {error}")
                    
                    return render(request, "add_contract.html", {
                        'contract_form': contract_form,
                        'trademark_formset': TrademarkFormSet(prefix='trademark', queryset=TrademarkService.objects.none()),
                        'copyright_formset': CopyrightFormSet(prefix='copyright', queryset=CopyrightService.objects.none()),
                        'business_form': BusinessRegistrationForm(),
                        'investment_form': form,  # Giữ form
                        'other_form': OtherServiceForm(),
                    })

                obj = form.save(commit=False)
                obj.contract = contract
                obj.save()
                print("✅ Saved investment")

            else:  # khac
                form = OtherServiceForm(request.POST, request.FILES)
                if not form.is_valid():
                    contract.delete()
                    for field, errors in form.errors.items():
                        for error in errors:
                            field_label = form.fields.get(field).label if field in form.fields else field
                            messages.error(request, f"Dịch vụ khác - {field_label}: {error}")
                    
                    return render(request, "add_contract.html", {
                        'contract_form': contract_form,
                        'trademark_formset': TrademarkFormSet(prefix='trademark', queryset=TrademarkService.objects.none()),
                        'copyright_formset': CopyrightFormSet(prefix='copyright', queryset=CopyrightService.objects.none()),
                        'business_form': BusinessRegistrationForm(),
                        'investment_form': InvestmentForm(),
                        'other_form': form,  # Giữ form
                    })

                obj = form.save(commit=False)
                obj.contract = contract
                obj.save()
                print("✅ Saved other service")

            # ===== HANDLE PREPAID PAYMENT =====
            if contract.prepaid_amount and contract.prepaid_amount > 0:
                PaymentInstallment.objects.create(
                    contract=contract,
                    amount=contract.contract_value,
                    paid_amount=contract.prepaid_amount,
                    is_paid=contract.prepaid_amount >= contract.contract_value
                )


            # ===== UPDATE CUSTOMER STATUS =====
            customer = contract.customer
            customer.status = 'pending'
            customer.save()
            print(f"✅ Updated customer status: {customer.customer_code}")

            print("\n" + "=" * 60)
            print("✅ CONTRACT CREATED SUCCESSFULLY!")
            print("=" * 60 + "\n")

            messages.success(request, "✅ Tạo hợp đồng thành công!")
            return redirect('contract_detail', id=contract.id)

        except Exception as e:
            import traceback
            print("\n" + "=" * 60)
            print("❌ ERROR OCCURRED")
            print("=" * 60)
            print(f"Error: {str(e)}")
            print(traceback.format_exc())
            print("=" * 60 + "\n")

            # Rollback
            if contract.id:
                contract.delete()

            messages.error(request, f"❌ Có lỗi xảy ra: {str(e)}")
            return redirect('add_contract')

    # ===== GET REQUEST =====
    print("\n📄 GET REQUEST - Rendering empty form")
    return render(request, "add_contract.html", {
        'contract_form': ContractForm(),
        'trademark_formset': TrademarkFormSet(prefix='trademark', queryset=TrademarkService.objects.none()),
        'copyright_formset': CopyrightFormSet(prefix='copyright', queryset=CopyrightService.objects.none()),
        'business_form': BusinessRegistrationForm(),
        'investment_form': InvestmentForm(),
        'other_form': OtherServiceForm(),
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
from django.db.models import QuerySet
def contract_detail(request, id):
    contract = get_object_or_404(Contract, id=id)
    installments = contract.installments.all()

    # ✅ ĐẾM SỐ ĐỢT ĐÃ TRẢ
    paid_count = installments.filter(is_paid=True).count()

    # ==========================
    # LẤY DỊCH VỤ
    # ==========================


    service: QuerySet
    if contract.service_type == "nhanhieu":
        service = contract.trademarks.all()
    elif contract.service_type == "banquyen":
        service = contract.copyrights.all()
    elif contract.service_type == "dkkd":
        service = BusinessRegistrationService.objects.filter(contract=contract)
    elif contract.service_type == "dautu":
        service = InvestmentService.objects.filter(contract=contract)
    else:
        service = OtherService.objects.filter(contract=contract)

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
        installment_id = request.POST.get("installment_id")
        paid_amount_raw = request.POST.get("paid_amount")

        # Kiểm tra dữ liệu đầu vào
        if not installment_id or not paid_amount_raw:
            messages.error(request, "❌ Thiếu thông tin thanh toán")
            return redirect("contract_detail", id=contract.id)

        try:
            paid_amount = Decimal(paid_amount_raw)
            
            # Tìm đợt thanh toán
            ins = contract.installments.filter(id=installment_id).first()
            
            if ins:
                # 1. Cập nhật số tiền vào đợt trả góp
                ins.paid_amount += paid_amount
                if ins.paid_amount >= ins.amount:
                    ins.is_paid = True
                    ins.paid_date = date.today()
                ins.save()

                # 2. 🔥 GHI LỊCH SỬ (Dòng code bạn hỏi gắn ở đây)
                PaymentLog.objects.create(
                    contract=contract,
                    installment=ins,
                    amount_paid=paid_amount
                )

                # 3. Cập nhật status contract 
                # (Vì remaining_amount là @property nên nó sẽ tự tính lại sau khi ins.save())
                if contract.remaining_amount <= 0:
                    contract.status = "completed"
                    contract.save(update_fields=["status"])

                messages.success(request, "✅ Đã lưu thanh toán và lịch sử giao dịch")
                return redirect("contract_detail", id=contract.id)

        except Exception as e:
            messages.error(request, f"❌ Có lỗi xảy ra: {str(e)}")
            return redirect("contract_detail", id=contract.id)


    return render(request, "contract_detail.html", {
        "contract": contract,
        "service": service,
        "installments": installments,
        "paid_count": paid_count,
    })


# ===============================================
# CONTRACT EDIT (ĐÃ SỬA - CẬP NHẬT TRẠNG THÁI)
# ===============================================
def contract_edit(request, id):
    contract = get_object_or_404(Contract, id=id)

    contract_form = None
    service_form = None
    service_formset = None

    # ==========================
    # XÁC ĐỊNH DỊCH VỤ
    # ==========================
    FormSetClass = None
    ServiceForm = None
    service = None
    queryset = None
    prefix = None

    if contract.service_type == "nhanhieu":
        FormSetClass = TrademarkFormSet
        queryset = TrademarkService.objects.filter(contract=contract)
        prefix = "trademark"

    elif contract.service_type == "banquyen":
        FormSetClass = CopyrightFormSet
        queryset = CopyrightService.objects.filter(contract=contract)
        prefix = "copyright"

    elif contract.service_type == "dkkd":
        service = get_object_or_404(BusinessRegistrationService, contract=contract)
        ServiceForm = BusinessRegistrationForm

    elif contract.service_type == "dautu":
        service = get_object_or_404(InvestmentService, contract=contract)
        ServiceForm = InvestmentForm

    else:  # khac
        service = get_object_or_404(OtherService, contract=contract)
        ServiceForm = OtherServiceForm

    # ==========================
    # POST
    # ==========================
    if request.method == "POST":
        contract_form = ContractForm(request.POST, instance=contract)
        lock_contract_fields(contract_form)

        if FormSetClass:
            service_formset = FormSetClass(
                request.POST,
                request.FILES,
                queryset=queryset,
                prefix=prefix
            )

            if contract_form.is_valid() and service_formset.is_valid():
                contract_form.save()

                instances = service_formset.save(commit=False)
                for obj in instances:
                    obj.contract = contract
                    obj.save()

                for obj in service_formset.deleted_objects:
                    obj.delete()

                messages.success(request, "✅ Cập nhật hợp đồng thành công!")
                return redirect("contract_detail", id=contract.id)

        else:
            service_form = ServiceForm(
                request.POST,
                request.FILES,
                instance=service
            )

            if contract_form.is_valid() and service_form.is_valid():
                contract_form.save()
                service_form.save()

                messages.success(request, "✅ Cập nhật hợp đồng thành công!")
                return redirect("contract_detail", id=contract.id)

    # ==========================
    # GET
    # ==========================
    else:
        contract_form = ContractForm(instance=contract)
        lock_contract_fields(contract_form)

        if FormSetClass:
            service_formset = FormSetClass(
                queryset=queryset,
                prefix=prefix
            )
        else:
            service_form = ServiceForm(instance=service)

    # ==========================
    # RENDER
    # ==========================
    return render(request, "contract_edit.html", {
        "contract": contract,
        "contract_form": contract_form,
        "service_formset": service_formset,  # 🔥 KHỚP TEMPLATE
        "service_form": service_form,
    })




# ===============================================
# DOWNLOAD CERTIFICATE
# ===============================================
def download_certificate(request, id):
    contract = get_object_or_404(Contract, id=id)

    if contract.service_type == "nhanhieu":
        service = contract.trademarks.first()
        if not service or not service.certificate_file:
            raise Http404("Không có giấy chứng nhận")

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

# ===============================================
# CONTRACT SEARCH (NHÃN HIỆU)
# ===============================================
from django.db.models import Q

def contract_search(request):
    q = request.GET.get('q', '').strip()

    # ✅ chỉ hợp đồng đăng ký nhãn hiệu
    contracts = Contract.objects.filter(
        service_type='nhanhieu'
    ).select_related('customer').order_by('-created_at')

    if q:
        contracts = contracts.filter(
            Q(contract_no__icontains=q) |                 # mã hợp đồng
            Q(customer__customer_code__icontains=q) |     # mã KH
            Q(customer__name__icontains=q)                # tên KH
        )

    return render(request, 'contract_search.html', {
        'contracts': contracts,
        'q': q
    })

# ===============================================
# Bản quyền tác giả
# ===============================================
from django.db.models import Q

def contract_copyright_search(request):
    q = request.GET.get('q', '').strip()

    contracts = Contract.objects.filter(
        service_type='banquyen'
    )

    if q:
        contracts = contracts.filter(
            Q(contract_no__icontains=q) |
            Q(customer__customer_code__icontains=q) |
            Q(customer__name__icontains=q)
        )

    contracts = contracts.order_by('-created_at')

    return render(request, 'contract_copyright_search.html', {
        'contracts': contracts,
        'q': q
    })

# ===============================================
# dkkq search
# ===============================================

def contract_business_search(request):
    q = request.GET.get('q', '').strip()

    contracts = Contract.objects.filter(
        service_type='dkkd'
    )

    if q:
        contracts = contracts.filter(
            Q(contract_no__icontains=q) |
            Q(customer__customer_code__icontains=q) |
            Q(customer__name__icontains=q)
        )

    contracts = contracts.order_by('-created_at')

    return render(request, 'contract_business_search.html', {
        'contracts': contracts,
        'q': q
    })
# ===============================================
# ĐK đầu tư
# ===============================================
def contract_investment_search(request):
    q = request.GET.get('q', '').strip()

    contracts = Contract.objects.filter(
        service_type='dautu'
    )

    if q:
        contracts = contracts.filter(
            Q(contract_no__icontains=q) |
            Q(customer__customer_code__icontains=q) |
            Q(customer__name__icontains=q)
        )

    contracts = contracts.order_by('-created_at')

    return render(request, 'contract_investment_search.html', {
        'contracts': contracts,
        'q': q
    })

# ===============================================
# Dịch Vụ Khác
# ===============================================
def contract_other_service_search(request):
    q = request.GET.get('q', '').strip()

    contracts = Contract.objects.filter(
        service_type='khac'   # ✅ DỊCH VỤ KHÁC
    )

    if q:
        contracts = contracts.filter(
            Q(contract_no__icontains=q) |
            Q(customer__customer_code__icontains=q) |
            Q(customer__name__icontains=q)
        )

    contracts = contracts.order_by('-created_at')

    return render(request, 'contract_other_service_search.html', {
        'contracts': contracts,
        'q': q
    })