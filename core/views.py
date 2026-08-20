from django.middleware.csrf import get_token
from django.shortcuts import render
import requests

MIB_URL = "http://91.90.216.68:9012"
KATM_URL = "http://91.90.216.68:9013"

_MISSING = object()

TRANSLATIONS = {
    "ru": {
        "lang_code": "ru",
        "doc_title": "Верификация и кредитный скоринг",
        "portal_badge": "Портал верификации",
        "header_title": "Верификация ПИНФЛ / КАТМ",
        "header_subtitle": "Введите ПИНФЛ или загрузите официальный PDF-отчет КАТМ для автоматизированного комплаенс-анализа.",
        "tab_pinfl": "ПИНФЛ",
        "tab_katm_pdf": "КАТМ PDF",
        "pinfl_label": "14-значный ПИНФЛ",
        "pinfl_placeholder": "31201991234567",
        "pinfl_hint": "Введите персональный идентификационный номер физического лица.",
        "katm_report_label": "Отчет КАТМ (.pdf)",
        "click_to_upload": "Нажмите для загрузки PDF КАТМ",
        "max_file_size": "Максимальный размер файла: 10 МБ",
        "run_verification": "Запустить проверку",
        "results_title": "Результаты проверки",
        "results_subtitle": "Статус автоматических правил валидации",
        "checks_run": "проверок выполнено",
        "pass": "Пройдено",
        "fail": "Не пройдено",
        "no_data": "Нет данных",
        "no_results_title": "Нет результатов для отображения",
        "no_results_subtitle": "Отправьте ПИНФЛ или отчет КАТМ для просмотра критериев и оценки.",
        "days": "дн.",
        "sum": "сум",
        "err_pinfl_length": "ПИНФЛ должен состоять ровно из 14 цифр.",
        "err_mib_prefix": "Ошибка при получении данных МИБ: ",
        "err_no_file": "Пожалуйста, выберите PDF-файл отчета КАТМ для загрузки.",
        "err_no_pinfl_in_pdf": "Не удалось извлечь ПИНФЛ из загруженного PDF-файла КАТМ.",
        "err_katm_prefix": "Ошибка при обработке файла КАТМ: ",
        # Rule keys
        "rule_mib_fly": "МИБ: Запрет на выезд за границу",
        "rule_mib_fly_has": "Имеется запрет",
        "rule_mib_fly_none": "Запрет отсутствует",
        "rule_mib_history": "МИБ: Наличие исполнительных производств / негативная история",
        "rule_mib_history_has": "Имеется негативная история",
        "rule_mib_history_none": "История чистая",
        "rule_mib_admin": "МИБ: Административные штрафы (Лимит: ≤ 500 000 сум)",
        "rule_mib_debt": "МИБ: Взыскание задолженностей (Лимит: ≤ 200 000 сум)",
        "rule_katm_score": "КАТМ: Скоринг балл (> 200)",
        "rule_katm_prin_days": "КАТМ: Макс. дней просрочки по осн. долгу (≤ 150 дней)",
        "rule_katm_cont_days": "КАТМ: Макс. непрерывных дней просрочки по % (≤ 120 дней)",
        "rule_katm_prin_amount": "КАТМ: Макс. сумма просрочки по осн. долгу (≤ 5 000 000 сум)",
        "rule_katm_pct_amount": "КАТМ: Макс. сумма просрочки по % (≤ 3 000 000 сум)",
        "rule_katm_lti": "КАТМ: Долговая нагрузка (LTI ≤ 30%)",
        "export_pdf": "Экспорт PDF",
        "clear": "Очистить",
    },
    "uz_lat": {
        "lang_code": "uz",
        "doc_title": "Verifikatsiya va kredit tekshiruvi",
        "portal_badge": "Verifikatsiya portali",
        "header_title": "JShShIR / KATM Verifikatsiyasi",
        "header_subtitle": "Avtomatlashtirilgan tahlil uchun JShShIR kiriting yoki rasmiy KATM PDF hisobotini yuklang.",
        "tab_pinfl": "JShShIR",
        "tab_katm_pdf": "KATM PDF",
        "pinfl_label": "14 xonali JShShIR",
        "pinfl_placeholder": "31201991234567",
        "pinfl_hint": "Jismoniy shaxsning shaxsiy identifikatsiya raqamini kiriting.",
        "katm_report_label": "KATM hisoboti (.pdf)",
        "click_to_upload": "KATM PDF faylini yuklash uchun bosing",
        "max_file_size": "Faylning maksimal hajmi: 10 MB",
        "run_verification": "Tekshiruvni boshlash",
        "results_title": "Tekshiruv natijalari",
        "results_subtitle": "Avtomatik tekshirish qoidalari holati",
        "checks_run": "ta tekshiruv o'tkazildi",
        "pass": "O'tdi",
        "fail": "O'tmadi",
        "no_data": "Ma'lumot yo'q",
        "no_results_title": "Ko'rsatish uchun natijalar yo'q",
        "no_results_subtitle": "Mezonlar va ballarni ko'rish uchun JShShIR yoki KATM hujjatini yuboring.",
        "days": "kun",
        "sum": "so'm",
        "err_pinfl_length": "JShShIR roppa-rosa 14 ta raqamdan iborat bo'lishi kerak.",
        "err_mib_prefix": "MIB ma'lumotlarini olishda xatolik: ",
        "err_no_file": "Iltimos, yuklash uchun KATM hisoboti PDF faylini tanlang.",
        "err_no_pinfl_in_pdf": "Yuklangan KATM PDF faylidan JShShIR aniqlanmadi.",
        "err_katm_prefix": "KATM faylini qayta ishlashda xatolik: ",
        # Rule keys
        "rule_mib_fly": "MIB: Chet elga chiqishga taqiq",
        "rule_mib_fly_has": "Taqiq mavjud",
        "rule_mib_fly_none": "Taqiq mavjud emas",
        "rule_mib_history": "MIB: Ijro ishlari / salbiy tarix mavjudligi",
        "rule_mib_history_has": "Salbiy tarix mavjud",
        "rule_mib_history_none": "Tarixi toza",
        "rule_mib_admin": "MIB: Ma'muriy jarimalar (Cheklov: ≤ 500 000 so'm)",
        "rule_mib_debt": "MIB: Qarzdorlikni undirish (Cheklov: ≤ 200 000 so'm)",
        "rule_katm_score": "KATM: Skoring bali (> 200)",
        "rule_katm_prin_days": "KATM: Asosiy qarz bo'yicha maks. kechikish kunlari (≤ 150 kun)",
        "rule_katm_cont_days": "KATM: Foizlar bo'yicha maks. uzluksiz kechikish kunlari (≤ 120 kun)",
        "rule_katm_prin_amount": "KATM: Asosiy qarz bo'yicha maks. kechikish summasi (≤ 5 000 000 so'm)",
        "rule_katm_pct_amount": "KATM: Foizlar bo'yicha maks. kechikish summasi (≤ 3 000 000 so'm)",
        "rule_katm_lti": "KATM: Qarz yuki (LTI ≤ 30%)",
        "export_pdf": "PDF Export",
        "clear": "Tozalash",
    },
    "uz_cyr": {
        "lang_code": "uz-Cyrl",
        "doc_title": "Верификация ва кредит текшируви",
        "portal_badge": "Верификация портали",
        "header_title": "ЖШШИР / КАТМ Верификацияси",
        "header_subtitle": "Автоматлаштирилган таҳлил учун ЖШШИР киритинг ёки расмий КАТМ PDF ҳисоботини юкланг.",
        "tab_pinfl": "ЖШШИР",
        "tab_katm_pdf": "КАТМ PDF",
        "pinfl_label": "14 хонали ЖШШИР",
        "pinfl_placeholder": "31201991234567",
        "pinfl_hint": "Жисмоний шахснинг шахсий идентификация рақамини киритинг.",
        "katm_report_label": "КАТМ ҳисоботи (.pdf)",
        "click_to_upload": "КАТМ PDF файлини юклаш учун босинг",
        "max_file_size": "Файлнинг максимал ҳажми: 10 МБ",
        "run_verification": "Текширувни бошлаш",
        "results_title": "Текширув натижалари",
        "results_subtitle": "Автоматик текшириш қоидалари ҳолати",
        "checks_run": "та текширув ўтказилди",
        "pass": "Ўтди",
        "fail": "Ўтмади",
        "no_data": "Маълумот йўқ",
        "no_results_title": "Кўрсатиш учун натижалар йўқ",
        "no_results_subtitle": "Мезонлар ва балларни кўриш учун ЖШШИР ёки КАТМ ҳужжатини юборинг.",
        "days": "кун",
        "sum": "сўм",
        "err_pinfl_length": "ЖШШИР роппа-роса 14 та рақамдан иборат бўлиши керак.",
        "err_mib_prefix": "МИБ маълумотларини олишда хатолик: ",
        "err_no_file": "Илтимос, юклаш учун КАТМ ҳисоботи PDF файлини танланг.",
        "err_no_pinfl_in_pdf": "Юкланган КАТМ PDF файлидан ЖШШИР аниқланмади.",
        "err_katm_prefix": "КАТМ файлини қайта ишлашда хатолик: ",
        # Rule keys
        "rule_mib_fly": "МИБ: Чет элга чиқишга тақиқ",
        "rule_mib_fly_has": "Тақиқ мавжуд",
        "rule_mib_fly_none": "Тақиқ мавжуд эмас",
        "rule_mib_history": "МИБ: Ижро ишлари / салбий тарих мавжудлиги",
        "rule_mib_history_has": "Салбий тарих мавжуд",
        "rule_mib_history_none": "Тарихи тоза",
        "rule_mib_admin": "МИБ: Маъмурий жарималар (Чеклов: ≤ 500 000 сўм)",
        "rule_mib_debt": "МИБ: Қарздорликни ундириш (Чеклов: ≤ 200 000 сўм)",
        "rule_katm_score": "КАТМ: Скоринг бали (> 200)",
        "rule_katm_prin_days": "КАТМ: Асосий қарз бўйича макс. кечикиш кунлари (≤ 150 кун)",
        "rule_katm_cont_days": "КАТМ: Фоизлар бўйича макс. узлуксиз кечикиш кунлари (≤ 120 кун)",
        "rule_katm_prin_amount": "КАТМ: Асосий қарз бўйича макс. кечикиш суммаси (≤ 5 000 000 сўм)",
        "rule_katm_pct_amount": "КАТМ: Фоизлар бўйича макс. кечикиш суммаси (≤ 3 000 000 сўм)",
        "rule_katm_lti": "КАТМ: Қарз юки (LTI ≤ 30%)",
        "export_pdf": "PDF Экспорт",
        "clear": "Тозалаш",
    }
}


def send_request(url):
    """Returns parsed JSON dict on success, or _MISSING on any failure
    (network error, timeout, non-2xx status, invalid JSON)."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception:
        return _MISSING


def check_fly_status(pinfl):
    response = send_request(f"{MIB_URL}/check_fly_limit/{pinfl}")
    if response is _MISSING:
        return _MISSING
    return response.get("has_limit", _MISSING)


def check_bad_history(pinfl):
    response = send_request(f"{MIB_URL}/check_loan_history/{pinfl}")
    if response is _MISSING:
        return _MISSING
    return response.get("has_history", _MISSING)


def check_debt(pinfl):
    response = send_request(f"{MIB_URL}/check_debt/{pinfl}")
    if response is _MISSING:
        return _MISSING
    val = response.get("amounts_by_category", _MISSING)
    if val is _MISSING or val is None:
        return _MISSING
    return val


def get_katm_data(katm_file):
    files = {
        "file": (katm_file.name, katm_file.file, katm_file.content_type)
    }
    response = requests.post(f"{KATM_URL}/extract", files=files, timeout=15)
    response.raise_for_status()
    return response.json()


def _field_or_no_data(t, key, container, field, cast, fmt, limit_check):
    """Builds a single result row. Shows 'no_data' status if the field
    is missing or null in the source payload, instead of silently
    defaulting to 0 and reporting a false pass."""
    raw = container.get(field, _MISSING) if container is not _MISSING else _MISSING
    if raw is _MISSING or raw is None:
        return {"key": t[key], "value": t["no_data"], "status": "no_data"}
    try:
        val = cast(raw)
    except (TypeError, ValueError):
        return {"key": t[key], "value": t["no_data"], "status": "no_data"}
    return {"key": t[key], "value": fmt(val), "status": "pass" if limit_check(val) else "fail"}


def evaluate_mib(pinfl, t):
    results = []

    # 1. Fly limit
    has_fly_limit = check_fly_status(pinfl)
    if has_fly_limit is _MISSING:
        results.append({"key": t["rule_mib_fly"], "value": t["no_data"], "status": "no_data"})
    else:
        results.append({
            "key": t["rule_mib_fly"],
            "value": t["rule_mib_fly_has"] if has_fly_limit else t["rule_mib_fly_none"],
            "status": "fail" if has_fly_limit else "pass",
        })

    # 2. Executive / negative history
    has_bad_history = check_bad_history(pinfl)
    if has_bad_history is _MISSING:
        results.append({"key": t["rule_mib_history"], "value": t["no_data"], "status": "no_data"})
    else:
        results.append({
            "key": t["rule_mib_history"],
            "value": t["rule_mib_history_has"] if has_bad_history else t["rule_mib_history_none"],
            "status": "fail" if has_bad_history else "pass",
        })

    # 3 & 4. Debt categories
    debts = check_debt(pinfl)
    if debts is _MISSING:
        debts = []

    admin_fine_total = 0.0
    recovery_debt_total = 0.0

    for item in debts:
        name = (item.get("name") or "").lower()
        amount = float(item.get("amount", 0) or 0)

        if "маъмурий" in name or "ma'muriy" in name or "административ" in name:
            admin_fine_total += amount
        elif "ундириш" in name or "ундирув" in name or "undirish" in name or "взыскан" in name:
            recovery_debt_total += amount

    results.append({
        "key": t["rule_mib_admin"],
        "value": f"{admin_fine_total:,.0f} {t['sum']}",
        "status": "pass" if admin_fine_total <= 500_000 else "fail",
    })

    results.append({
        "key": t["rule_mib_debt"],
        "value": f"{recovery_debt_total:,.0f} {t['sum']}",
        "status": "pass" if recovery_debt_total <= 200_000 else "fail",
    })

    return results


def evaluate_katm(katm_data, t):
    results = []

    scoring = katm_data.get("scoring_ciac")
    scoring = scoring if scoring is not None else _MISSING

    overview = katm_data.get("general_overview_open_and_closed")
    overview = overview if overview is not None else _MISSING

    incomes_list = katm_data.get("incomes") or {}
    inps_list = incomes_list.get("inps") or [{}]
    incomes = inps_list[0] if inps_list else {}

    # 1. Scoring
    results.append(_field_or_no_data(
        t, "rule_katm_score", scoring, "credit_score", float,
        lambda v: f"{v:.0f}", lambda v: v > 200,
    ))

    # 2. Max Principal Overdue Days
    results.append(_field_or_no_data(
        t, "rule_katm_prin_days", overview, "max_principal_overdue_days", int,
        lambda v: f"{v} {t['days']}", lambda v: v <= 150,
    ))

    # 3. Max Continuous Overdue Days Pct
    results.append(_field_or_no_data(
        t, "rule_katm_cont_days", overview, "max_continuous_overdue_days_pct", int,
        lambda v: f"{v} {t['days']}", lambda v: v <= 120,
    ))

    # 4. Max Principal Overdue Amount
    results.append(_field_or_no_data(
        t, "rule_katm_prin_amount", overview, "max_principal_overdue_amount", float,
        lambda v: f"{v:,.0f} {t['sum']}", lambda v: v <= 5_000_000,
    ))

    # 5. Max Pct Overdue Amount
    results.append(_field_or_no_data(
        t, "rule_katm_pct_amount", overview, "max_overdue_amount_pct", float,
        lambda v: f"{v:,.0f} {t['sum']}", lambda v: v <= 3_000_000,
    ))

    # 6. LTI — needs two fields (avg payment + total income), handled explicitly
    avg_payment_raw = overview.get("average_monthly_payment", _MISSING) if overview is not _MISSING else _MISSING
    total_income_raw = incomes.get("total", _MISSING)

    if avg_payment_raw is _MISSING or avg_payment_raw is None or \
       total_income_raw is _MISSING or total_income_raw is None:
        results.append({"key": t["rule_katm_lti"], "value": t["no_data"], "status": "no_data"})
    else:
        average_monthly_payment = float(avg_payment_raw or 0)
        total_income = float(total_income_raw or 0)
        periods = sum(1 for p in (incomes.get("monthly") or []) if p.get("amount", 0) > 0)
        average_income = (total_income / periods) if periods > 0 else 0
        ratio = (average_monthly_payment / average_income) if average_income > 0 else 0
        results.append({
            "key": t["rule_katm_lti"],
            "value": f"{ratio * 100:.1f} %",
            "status": "pass" if ratio <= 0.3 else "fail",
        })

    return results


def main(request):
    lang = request.GET.get("lang") or request.POST.get("lang") or "ru"
    if lang not in TRANSLATIONS:
        lang = "ru"

    t = TRANSLATIONS[lang]

    context = {
        "t": t,
        "lang": lang,
        "csrf_token": get_token(request),
        "active_tab": "pinfl",
        "results": None,
        "error": None,
    }

    if request.method == "POST":
        req_type = request.POST.get("type", "pinfl")
        context["active_tab"] = req_type

        # Option 1: PINFL only (MIB)
        if req_type == "pinfl":
            pinfl = request.POST.get("pinfl", "").strip()
            context["pinfl_val"] = pinfl

            if not pinfl or len(pinfl) != 14 or not pinfl.isdigit():
                context["error"] = t["err_pinfl_length"]
            else:
                try:
                    context["results"] = evaluate_mib(pinfl, t)
                except Exception as e:
                    context["error"] = f"{t['err_mib_prefix']}{str(e)}"

        # Option 2: KATM PDF + MIB
        elif req_type == "katm_pdf":
            katm_file = request.FILES.get("katm_pdf")

            if not katm_file:
                context["error"] = t["err_no_file"]
            else:
                try:
                    katm_data = get_katm_data(katm_file)
                    pinfl = (katm_data.get("credit_information_subject") or {}).get("personal_id_number")

                    if not pinfl:
                        context["error"] = t["err_no_pinfl_in_pdf"]
                    else:
                        context["pinfl_val"] = pinfl
                        katm_results = evaluate_katm(katm_data, t)
                        mib_results = evaluate_mib(str(pinfl), t)
                        context["results"] = katm_results + mib_results
                except Exception as e:
                    context["error"] = f"{t['err_katm_prefix']}{str(e)}"

    return render(request, "main.html", context)
