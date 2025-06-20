from .forms import CustomLoginForm
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.shortcuts import redirect, render
from django.views import View
from django.contrib.auth.decorators import login_required
from django.views.generic import DetailView
from django.contrib.auth.forms import AuthenticationForm
from django.conf import settings
import google.generativeai as genai
import json
import re
from .models import ChatHistory, WorkoutPlan
from users.models import CustomUser as User
from django.views.decorators.http import require_GET
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_decode
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

# Gemini API yapılandırması
genai.configure(api_key=settings.GEMINI_API_KEY)


# Zararlı cümleleri filtrele
UNWANTED_PHRASES = [
    "ben bir yapay zekâ modeliyim", "ben bir yapay zeka modeliyim",
    "doktor değilim", "tıbbi", "önce doktorunuza danışın",
    "önce bir uzmana danışın", "uzman", "bir uzmana danışmanız gerekebilir",
    "sağlık profesyoneline danışın", "doğru bilgi için uzmana danışın",
    "bilgi vermem uygun değil", "sağlığınız için riskli olabilir"
]

def clean_response_text(text):
    for phrase in UNWANTED_PHRASES:
        text = text.replace(phrase, "")
    return text.strip()

@csrf_exempt
@login_required
def chat_with_gemini(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_input = data.get('message', '')
        user = request.user

        # Günler (kontrol için dışarı alındı)
        days_tr = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        days_en = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        profile_info = f"Yaş: {user.age}, Boy: {user.height} cm, Kilo: {user.weight} kg."

        messages = [
    {
        "role": "user",
        "parts": [
            f"Sen GymBot adında bir kişisel antrenör botsun. Kullanıcı bilgileri: {profile_info}. "
            f"Aşağıdaki kurallara **harfi harfine** uy:\n"
            f"1. Her gün ayrı ayrı yazılmalı. 'Pazartesi:', 'Salı:' gibi başlayacak.\n"
            f"2. HER GÜN maksimum 2-3 cümle içermeli.\n"
            f"3. Progresyon, gelişim açıklamaları, hafta 2-4+, genel fitness tavsiyeleri vb. bilgiler **hiçbir günün altında yer almamalı**.\n"
            f"4. Bu tarz bilgiler sadece 'Genel Notlar:' veya 'Weekly Notes:' başlığı altında verilmelidir. Bu bölüm **günlerden sonra gelmeli**.\n"
            f"5. Örnek format:\n\n"
            f"Pazartesi: Yürüyüş 30 dk. Şınav 3x10.\nSalı: Dinlenme.\n...\nGenel Notlar: Her hafta kardiyo süresini artırın. Kuvvet için set tekrarlarını artırabilirsiniz.\n"
            f"6. Hiçbir cümlede yıldız (*), bold, markdown veya biçimsel karakter olmasın.\n"
            f"7. Yazım dili eğer kullanıcı türkçe konuşuyorsa türkçe , ingilizce konuşuyorsa ingilizce olmalı\n"
        ]
    }
    ]

        history = ChatHistory.objects.filter(user=user).order_by('-timestamp')[:5]
        history = list(reversed(history))

        for entry in history:
            messages.append({
                "role": "user" if entry.role == "user" else "model",
                "parts": [entry.message]
            })

        messages.append({"role": "user", "parts": [user_input]})

        try:
            model = genai.GenerativeModel('gemini-1.5-pro')
            chat = model.start_chat(history=messages)
            response = chat.send_message(user_input)
            cleaned_text = clean_response_text(response.text)

            # İngilizce veya Türkçe gün varsa kayıt et
            if any(day in cleaned_text for day in days_tr + days_en):
                parse_and_save_workout_plan(user, cleaned_text)

            # Sohbet geçmişini kaydet
            ChatHistory.objects.create(user=user, role="user", message=user_input)
            ChatHistory.objects.create(user=user, role="bot", message=cleaned_text)

            return JsonResponse({'response': cleaned_text})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

def parse_and_save_workout_plan(user, response_text):
    import re
    from .models import WorkoutPlan

    day_map = {
        "Pazartesi": "Pazartesi", "Salı": "Salı", "Çarşamba": "Çarşamba",
        "Perşembe": "Perşembe", "Cuma": "Cuma", "Cumartesi": "Cumartesi", "Pazar": "Pazar",
        "Monday": "Pazartesi", "Tuesday": "Salı", "Wednesday": "Çarşamba",
        "Thursday": "Perşembe", "Friday": "Cuma", "Saturday": "Cumartesi", "Sunday": "Pazar"
    }

    # Eğer Genel Notlar varsa önce ayır
    general_notes = ""
    if "Genel Notlar:" in response_text:
        parts = response_text.split("Genel Notlar:")
        response_text = parts[0].strip()
        general_notes = parts[1].strip()

    # Gün gün ayır
    pattern = r"(Pazartesi|Salı|Çarşamba|Perşembe|Cuma|Cumartesi|Pazar|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)[\s]*[:\-–][\s]*(.*?)(?=\n(?:Pazartesi|Salı|Çarşamba|Perşembe|Cuma|Cumartesi|Pazar|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)[\s]*[:\-–]|\Z)"
    matches = re.findall(pattern, response_text, re.IGNORECASE | re.DOTALL)

    WorkoutPlan.objects.filter(user=user).delete()

    for raw_day, raw_content in matches:
        day_key = raw_day.strip().capitalize()
        content = raw_content.strip()

        # Temizle
        content_cleaned = re.sub(r"[*_`]+", "", content)
        content_cleaned = re.sub(r"\s+", " ", content_cleaned).strip()

        if not content_cleaned or len(content_cleaned) < 5:
            continue

        day_tr = day_map.get(day_key, day_key)
        WorkoutPlan.objects.create(user=user, day=day_tr, content=content_cleaned)

    # Genel notlar varsa, ekstra kayıt olarak ekle
    if general_notes:
        general_cleaned = re.sub(r"[*_`]+", "", general_notes)
        WorkoutPlan.objects.create(user=user, day="Genel Notlar", content=general_cleaned.strip())


class RegisterView(View):
    def get(self, request):
        return render(request, "register.html")

    def post(self, request):
        username = request.POST.get("username")
        password = request.POST.get("password")
        email = request.POST.get("email")

        if not username or not password:
            return render(request, "register.html", {"error": "Tüm alanları doldurun."})

        if User.objects.filter(username=username).exists():
            return render(request, "register.html", {"error": "Kullanıcı adı zaten mevcut."})

        user = User.objects.create_user(username=username, password=password, email=email)
        user.full_name = username
        user.age = 25
        user.height = 170
        user.weight = 75
        user.save()
        return redirect("/api/users/login/")


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(View):
    def get(self, request):
        next_url = request.GET.get('next', '/')
        form = CustomLoginForm()
        return render(request, "login.html", {'form': form, 'next': next_url})

    def post(self, request):
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.POST.get('next', '/api/users/')
            return redirect(next_url)
        return render(request, "login.html", {'form': form})


class ProfileDetailView(DetailView):
    model = User
    template_name = 'profile_detail.html'
    context_object_name = 'user'

    def get_object(self):
        return self.request.user

class ProfileView(View):
    def get(self, request, *args, **kwargs):
        user = request.user
        return render(request, 'profile.html', {'user': user})

@login_required
def protected_view(request):
    return render(request, 'protected.html')

def home(request):
    return render(request, 'home.html')

@require_http_methods(["GET"])
def user_list(request):
    users = User.objects.all().values("id", "username", "email", "is_staff", "is_superuser")
    return JsonResponse(list(users), safe=False)

@require_http_methods(["GET"])
def logout_view(request):
    logout(request)
    return redirect('/api/users/')
@login_required
def admin_panel(request):
    language = request.session.get("language", "en")
    
    context = {
        "user": request.user,
        "language": language,
    }

    if request.user.is_superuser:
        context["all_users"] = User.objects.all()

    return render(request, "admin_panel.html", context)

@login_required
def admin_panel_view(request):
    language = getattr(request.user, "language", "en")  # varsayılan olarak en
    all_users = User.objects.all() if request.user.is_superuser else None
    plans = WorkoutPlan.objects.filter(user=request.user)

    return render(request, "adminpanel.html", {
        "plans": plans,
        "all_users": all_users,
        "language": language,
    })

@login_required
def calendar_view(request):
    user = request.user
    plans = WorkoutPlan.objects.filter(user=user)

    # Türkçe → İngilizce eşleştirme
    day_translations = {
        "Pazartesi": "Monday",
        "Salı": "Tuesday",
        "Çarşamba": "Wednesday",
        "Perşembe": "Thursday",
        "Cuma": "Friday",
        "Cumartesi": "Saturday",
        "Pazar": "Sunday",
    }

    # İngilizce karşılıklarıyla liste üret
    translated_plans = []
    for plan in plans:
        translated_plans.append({
            "day": day_translations.get(plan.day, plan.day),  # default = orijinal
            "content": plan.content,
            "id": plan.id,
            "done": plan.done,
        })

    return render(request, "calendar.html", {"plans": translated_plans})


@require_POST
@login_required
def update_user_info(request):
    user = request.user
    data = request.POST
    user.full_name = data.get("name", user.full_name)
    user.age = data.get("age", user.age)
    user.height = data.get("height", user.height)
    user.weight = data.get("weight", user.weight)
    user.save()
    return JsonResponse({"status": "success"})

@require_POST
@login_required
def toggle_done(request, plan_id):
    try:
        plan = WorkoutPlan.objects.get(id=plan_id, user=request.user)
        plan.done = not plan.done
        plan.save()
        return JsonResponse({"status": "success", "done": plan.done})
    except WorkoutPlan.DoesNotExist:
        return JsonResponse({"error": "Plan bulunamadı"}, status=404)

@require_POST
@login_required
def delete_plan(request, plan_id):
    WorkoutPlan.objects.filter(id=plan_id, user=request.user).delete()
    return JsonResponse({"status": "deleted"})

@require_POST
@login_required
def delete_all_plans(request):
    WorkoutPlan.objects.filter(user=request.user).delete()
    return JsonResponse({"status": "all_deleted"})



@csrf_exempt
@login_required
def update_language(request):
    if request.method == "POST":
        new_lang = request.POST.get("language")
        if new_lang in ["en", "tr"]:
            request.user.language = new_lang
            request.user.save()
            return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"})

from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.csrf import csrf_exempt
import json


@user_passes_test(lambda u: u.is_superuser)
def admin_update_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)

    if request.method == "GET":
        return JsonResponse({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "age": user.age,
            "height": user.height,
            "weight": user.weight
        })

    elif request.method == "POST":
        data = json.loads(request.body)
        user.username = data.get("username", user.username)
        user.email = data.get("email", user.email)
        user.full_name = data.get("full_name", user.full_name)
        user.age = data.get("age", user.age)
        user.height = data.get("height", user.height)
        user.weight = data.get("weight", user.weight)
        user.save()
        return JsonResponse({"status": "updated"})

    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)

@user_passes_test(lambda u: u.is_superuser)
def admin_delete_user(request, user_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=405)
    try:
        user = User.objects.get(id=user_id)
        user.delete()
        return JsonResponse({"status": "ok"})
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)



@user_passes_test(lambda u: u.is_superuser)
def admin_get_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        return JsonResponse({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "age": user.age,
            "height": user.height,
            "weight": user.weight
        })
    except User.DoesNotExist:
        return JsonResponse({"status": "error", "message": "User not found"}, status=404)

@require_GET
@login_required
def calendar_json(request):
    user = request.user
    plans = WorkoutPlan.objects.filter(user=user)

    day_translations = {
        "Pazartesi": "Monday", "Salı": "Tuesday", "Çarşamba": "Wednesday",
        "Perşembe": "Thursday", "Cuma": "Friday", "Cumartesi": "Saturday", "Pazar": "Sunday",
        "Genel Notlar": "General Notes"
    }

    data = []
    for plan in plans:
        data.append({
            "day": day_translations.get(plan.day, plan.day),
            "content": plan.content,
            "id": plan.id,
            "done": plan.done
        })

    return JsonResponse(data, safe=False)        
@csrf_exempt
def forgot_password_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        user_model = get_user_model()
        try:
            user = user_model.objects.get(email=email)
        except user_model.DoesNotExist:
            return render(request, "forgot_password.html", {"error": "E-posta bulunamadı."})

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        reset_url = f"{request.scheme}://{request.get_host()}/api/users/reset-password-confirm/{uid}/{token}/"

        message = render_to_string("reset_email_template.txt", {
            "username": user.username,
            "reset_url": reset_url,
        })

        send_mail(
            "Your Password Reset Link/Şifre Sıfırlama Bağlantınız",
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
        return render(request, "forgot_password.html", {"success": "Reset email sent."})

    return render(request, "forgot_password.html")    


@csrf_exempt
def reset_password_confirm_view(request, uidb64, token):
    User = get_user_model()
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if request.method == 'POST':
        new_password = request.POST.get("password")
        if user is not None and default_token_generator.check_token(user, token):
            user.set_password(new_password)
            user.save()
            return render(request, "reset_password_complete.html", {"success": "Your password has been updated successfully."})
        else:
            return render(request, "reset_password_confirm.html", {"error": "Invalid link."})

    return render(request, "reset_password_confirm.html", {"uid": uidb64, "token": token})    


@csrf_exempt
@require_POST
def api_login_view(request):
    try:
        data = json.loads(request.body)
        email = data.get("email")
        password = data.get("password")

        user = authenticate(request, username=email, password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return JsonResponse({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user_id': user.id,
                'email': user.email,
                'username': user.username,
            })
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)