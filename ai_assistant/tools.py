"""Permission-aware tools exposed to the Persian assistant."""
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.utils import timezone
from django.db import transaction

from creator_program.models import Program
from creator_project.models import Project
from creator_subproject.models import SubProject

from .models import AIPendingAction
from .permissions import can_write_object, resolve_visible


FIELD_CATALOG = {
    "program": {
        "title": ("عنوان طرح", "نام رسمی و قابل گزارش طرح.", "مثال: احداث پایگاه امداد"),
        "program_type": ("نوع طرح", "دسته‌بندی اصلی طرح که برای گزارش‌گیری استفاده می‌شود.", "مثال: پایگاه امداد کوهستانی"),
        "license_state": ("وضعیت مجوز دفترچه توجیهی", "مشخص می‌کند مجوز دفترچه توجیهی صادر شده، در دست اقدام یا موجود نیست.", "دارد"),
        "license_code": ("کد مجوز دفترچه توجیهی", "شماره مرجع مجوز دفترچه توجیهی طرح.", "۱۴۰۳/۱۲۳۴"),
        "province": ("استان", "استان محل طرح؛ تغییر آن ممکن است محدوده دسترسی و گزارش‌ها را تغییر دهد.", "تهران"),
        "city": ("شهر", "شهر محل اجرای طرح.", "کرج"),
        "address": ("آدرس", "نشانی پستی محل اجرای طرح.", "استان تهران، شهرستان ..."),
        "longitude": ("طول جغرافیایی", "مختصات شرقی/غربی مکان به درجه اعشاری، با حداکثر شش رقم اعشار.", "51.3890"),
        "latitude": ("عرض جغرافیایی", "مختصات شمالی/جنوبی مکان به درجه اعشاری، با حداکثر شش رقم اعشار.", "35.6892"),
        "description": ("توضیحات", "شرح تکمیلی طرح، فرضیات یا نکات اجرایی.", "شرح تکمیلی"),
    },
    "project": {
        "name": ("نام پروژه", "نام قابل شناسایی پروژه داخل یک طرح.", "احداث انبار امدادی"),
        "project_type": ("نوع پروژه", "نوع عملیات پروژه، مانند احداث، تکمیل یا تعمیرات.", "احداث"),
        "area_size": ("عرصه", "مساحت زمین پروژه، معمولاً بر حسب مترمربع.", "1200"),
        "notables": ("اعیان", "مساحت زیربنای ساخته‌شده یا قابل ساخت، معمولاً بر حسب مترمربع.", "800"),
        "site_area": ("مساحت محوطه سازی", "مساحت عملیات محوطه‌سازی.", "500"),
        "wall_length": ("طول دیوارکشی", "طول دیوارکشی پروژه، معمولاً بر حسب متر.", "180"),
        "floor": ("طبقه", "تعداد طبقات پروژه.", "2"),
        "estimated_opening_time": ("تاریخ پایان پروژه", "تاریخ برنامه‌ریزی‌شده پایان پروژه.", "1405/06/30 یا 2026-09-21"),
        "physical_progress": ("پیشرفت فیزیکی", "درصد پیشرفت محاسبه‌شده پروژه؛ بهتر است از زیرپروژه‌ها محاسبه شود.", "45"),
    },
    "subproject": {
        "name": ("نام زیرپروژه", "نام مرحله یا بسته قراردادی.", "اجرای فونداسیون"),
        "project_stage": ("مرحله جاری پروژه", "مرحله فعلی اجرای زیرپروژه.", "فونداسیون"),
        "sub_project_number": ("اولویت زیرپروژه", "شماره/اولویت زیرپروژه در بازه ۱ تا ۱۰ در ساختار فعلی سامانه.", "1"),
        "is_suportting_charity": ("مشارکت خیرین", "مشخص می‌کند زیرپروژه با مشارکت خیرین انجام می‌شود یا خیر.", "دارد"),
        "state": ("وضعیت پروژه", "وضعیت قراردادی و اجرایی زیرپروژه.", "فعال"),
        "physical_progress": ("پیشرفت فیزیکی", "درصد پیشرفت واقعی زیرپروژه از صفر تا صد.", "35"),
        "remaining_work": ("کارهای باقیمانده", "شرح کارهایی که برای تکمیل زیرپروژه باقی مانده است.", "تکمیل تأسیسات"),
        "imagenary_duration": ("مدت تخمینی (روز)", "مدت تخمینی زیرپروژه بدون قرارداد، بر حسب روز.", "90"),
        "imagenrary_cost": ("هزینه تخمینی (ریال)", "برآورد هزینه زیرپروژه بدون قرارداد.", "15000000000"),
        "contract_start_date": ("تاریخ شروع قرارداد", "تاریخ شروع رسمی قرارداد.", "2026-01-01"),
        "contract_end_date": ("تاریخ پایان قرارداد", "تاریخ پایان رسمی قرارداد.", "2026-12-31"),
        "contract_amount": ("مبلغ قرارداد", "مبلغ پایه قرارداد به ریال.", "50000000000"),
        "contract_type": ("نوع قرارداد", "روش قراردادی انتخاب‌شده برای زیرپروژه.", "سرجمع"),
        "execution_method": ("روش اجرا", "روش انتخاب پیمانکار یا اجرای کار.", "مناقصه عمومی"),
        "contractor_name": ("نام پیمانکار", "نام شخص حقوقی یا حقیقی پیمانکار.", "شرکت ..."),
        "contractor_id": ("شناسه پیمانکار", "شناسه ثبت‌شده پیمانکار.", "123456789"),
        "has_consultant": ("وضعیت مشاور", "وجود یا عدم وجود مشاور برای زیرپروژه.", "دارد"),
        "consultant_name": ("نام مشاور", "نام مشاور پروژه.", "مهندسین مشاور ..."),
        "consultant_national_id": ("شناسه ملی مشاور", "شناسه ملی مشاور.", "10101234567"),
        "predicted_adjustment_amount": ("مجموع پیش‌بینی تعدیل", "برآورد مجموع تعدیل‌های مورد انتظار تا پایان پروژه به ریال.", "8000000000"),
    },
}

EDITABLE_FIELDS = {
    "program": set(FIELD_CATALOG["program"]) - {"province", "license_code"},
    "project": set(FIELD_CATALOG["project"]) - {"physical_progress"},
    "subproject": set(FIELD_CATALOG["subproject"]) - {"sub_project_number"},
}

MODEL_MAP = {"program": Program, "project": Project, "subproject": SubProject}


def explain_field(entity, field):
    data = FIELD_CATALOG.get(entity, {}).get(field)
    if not data:
        return None
    label, description, example = data
    return {"entity": entity, "field": field, "label": label,
            "description": description, "example": example,
            "editable_by_ai": field in EDITABLE_FIELDS.get(entity, set())}


def resolve_target(user, entity, object_id):
    model = MODEL_MAP.get(entity)
    if not model:
        raise ValueError("نوع موجودیت پشتیبانی نمی‌شود.")
    return resolve_visible(user, model, object_id)


def _coerce_value(obj, field, value):
    model_field = obj._meta.get_field(field)
    text = str(value).strip()
    if model_field.get_internal_type() in {"DecimalField", "IntegerField", "PositiveIntegerField"}:
        try:
            number = Decimal(text.replace(",", "").replace("٬", ""))
            if model_field.get_internal_type() != "DecimalField":
                number = int(number)
            return number
        except (InvalidOperation, ValueError):
            raise ValueError("مقدار عددی معتبر نیست.")
    if model_field.get_internal_type() == "DateField":
        from datetime import date
        try:
            return date.fromisoformat(text)
        except ValueError:
            raise ValueError("تاریخ باید به‌صورت میلادی YYYY-MM-DD ارسال شود.")
    choices = dict(model_field.choices or [])
    if choices and text not in choices:
        raise ValueError("این مقدار در گزینه‌های مجاز سامانه وجود ندارد.")
    return text


def preview_update(user, entity, object_id, field, value):
    if field not in EDITABLE_FIELDS.get(entity, set()):
        raise ValueError("این فیلد برای ویرایش AI مجاز نیست یا مقدار محاسباتی است.")
    obj = resolve_target(user, entity, object_id)
    if not can_write_object(user, obj):
        raise PermissionError("سطح دسترسی فعلی شما اجازه ویرایش این رکورد را نمی‌دهد.")
    if not hasattr(obj, field):
        raise ValueError("فیلد در موجودیت انتخاب‌شده وجود ندارد.")
    new_value = _coerce_value(obj, field, value)
    if field == "physical_progress" and not 0 <= float(new_value) <= 100:
        raise ValueError("پیشرفت فیزیکی باید بین صفر و صد باشد.")
    old_value = getattr(obj, field)
    payload = {
        "entity": entity, "object_id": obj.pk, "field": field,
        "field_label": explain_field(entity, field)["label"],
        "old_value": str(old_value if old_value is not None else ""),
        "new_value": str(new_value),
    }
    action = AIPendingAction.objects.create(
        user=user, payload=payload, expires_at=timezone.now() + timedelta(minutes=10)
    )
    payload["action_id"] = action.pk
    return payload


@transaction.atomic
def confirm_update(user, action_id):
    action = AIPendingAction.objects.select_for_update().get(
        pk=action_id, user=user, status="pending"
    )
    if action.expires_at < timezone.now():
        action.status = "expired"
        action.save(update_fields=["status"])
        raise ValueError("زمان تأیید این عملیات به پایان رسیده است.")
    data = action.payload
    obj = resolve_target(user, data["entity"], data["object_id"])
    if not can_write_object(user, obj):
        raise PermissionError("مجوز ویرایش این رکورد دیگر معتبر نیست.")
    current_value = str(getattr(obj, data["field"]) or "")
    if current_value != data["old_value"]:
        action.status = "conflict"
        action.save(update_fields=["status"])
        raise ValueError("مقدار رکورد پس از پیش‌نمایش تغییر کرده است؛ درخواست را دوباره بررسی کنید.")
    value = _coerce_value(obj, data["field"], data["new_value"])
    setattr(obj, data["field"], value)
    obj._update_user = user
    obj.save()
    action.status = "confirmed"
    action.confirmed_at = timezone.now()
    action.save(update_fields=["status", "confirmed_at"])
    return data
