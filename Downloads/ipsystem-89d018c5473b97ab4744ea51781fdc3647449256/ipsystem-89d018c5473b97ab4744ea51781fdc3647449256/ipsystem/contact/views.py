from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import redirect,render
from django.contrib import messages


def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        message_text = request.POST.get("message")

        subject = "Cảm ơn bạn đã liên hệ IPSystem"

        message = f"""
Xin chào {name},

Chúng tôi đã nhận được yêu cầu của bạn.

Thông tin bạn gửi:

Email: {email}
SĐT: {phone}

Nội dung:
{message_text}

Chúng tôi sẽ phản hồi sớm nhất.

IPSystem
"""

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],   # gửi cho khách hàng
            fail_silently=False,
        )

        messages.success(request, "Gửi thành công!")
        return redirect("contact:contact")

    return render(request, "contact/contact.html")