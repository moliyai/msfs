from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.views import LoginView, LogoutView
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.shortcuts import redirect
import requests
import json
from datetime import datetime

# Import your newly created models
from .models import VerificationItem, VerificationReport
# Import TRANSLATIONS
from .translations import TRANSLATIONS

MIB_URL = "http://91.90.216.68:9012"
KATM_URL = "http://91.90.216.68:9013"

_MISSING = object()


def send_request(url):
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
    raw = (
        container.get(field, _MISSING)
        if container is not _MISSING
        else _MISSING
    )
    if raw is _MISSING or raw is None:
        return {"key": t[key], "value": t["no_data"], "status": "no_data"}
    try:
        val = cast(raw)
    except (TypeError, ValueError):
        return {"key": t[key], "value": t["no_data"], "status": "no_data"}
    return {
        "key": t[key],
        "value": fmt(val),
        "status": "pass" if limit_check(val) else "fail",
    }


def evaluate_mib(pinfl, t):
    results = []

    has_fly_limit = check_fly_status(pinfl)
    if has_fly_limit is _MISSING:
        results.append(
            {"key": t["rule_mib_fly"], "value": t["no_data"], "status": "no_data"}
        )
    else:
        results.append(
            {
                "key": t["rule_mib_fly"],
                "value": (
                    t["rule_mib_fly_has"]
                    if has_fly_limit
                    else t["rule_mib_fly_none"]
                ),
                "status": "fail" if has_fly_limit else "pass",
            }
        )

    has_bad_history = check_bad_history(pinfl)
    if has_bad_history is _MISSING:
        results.append(
            {
                "key": t["rule_mib_history"],
                "value": t["no_data"],
                "status": "no_data",
            }
        )
    else:
        results.append(
            {
                "key": t["rule_mib_history"],
                "value": (
                    t["rule_mib_history_has"]
                    if has_bad_history
                    else t["rule_mib_history_none"]
                ),
                "status": "fail" if has_bad_history else "pass",
            }
        )

    debts = check_debt(pinfl)
    if debts is _MISSING:
        debts = []

    admin_fine_total = 0.0
    recovery_debt_total = 0.0

    for item in debts:
        name = (item.get("name") or "").lower()
        amount = float(item.get("amount", 0) or 0)

        if (
            "маъмурий" in name
            or "ma'muriy" in name
            or "административ" in name
        ):
            admin_fine_total += amount
        elif (
            "ундириш" in name
            or "ундирув" in name
            or "undirish" in name
            or "взыскан" in name
        ):
            recovery_debt_total += amount

    results.append(
        {
            "key": t["rule_mib_admin"],
            "value": f"{admin_fine_total:,.0f} {t['sum']}",
            "status": "pass" if admin_fine_total <= 500_000 else "fail",
        }
    )

    results.append(
        {
            "key": t["rule_mib_debt"],
            "value": f"{recovery_debt_total:,.0f} {t['sum']}",
            "status": "pass" if recovery_debt_total <= 200_000 else "fail",
        }
    )

    return results


def evaluate_katm(katm_data, t):
    results = []

    scoring = katm_data.get("scoring_ciac")
    scoring = scoring if scoring is not None else _MISSING

    overview = katm_data.get("general_overview_open_and_closed")
    overview = overview if overview is not None else _MISSING

    incomes_list = katm_data.get("incomes") or {}
    inps_list = incomes_list.get("combined") or {}
    incomes = inps_list if inps_list else {}

    results.append(
        _field_or_no_data(
            t,
            "rule_katm_score",
            scoring,
            "credit_score",
            float,
            lambda v: f"{v:.0f}",
            lambda v: v > 200,
        )
    )

    results.append(
        _field_or_no_data(
            t,
            "rule_katm_prin_days",
            overview,
            "max_principal_overdue_days",
            int,
            lambda v: f"{v} {t['days']}",
            lambda v: v <= 150,
        )
    )

    results.append(
        _field_or_no_data(
            t,
            "rule_katm_cont_days",
            overview,
            "max_continuous_overdue_days_pct",
            int,
            lambda v: f"{v} {t['days']}",
            lambda v: v <= 120,
        )
    )

    results.append(
        _field_or_no_data(
            t,
            "rule_katm_prin_amount",
            overview,
            "max_principal_overdue_amount",
            float,
            lambda v: f"{v:,.0f} {t['sum']}",
            lambda v: v <= 5_000_000,
        )
    )

    results.append(
        _field_or_no_data(
            t,
            "rule_katm_pct_amount",
            overview,
            "max_overdue_amount_pct",
            float,
            lambda v: f"{v:,.0f} {t['sum']}",
            lambda v: v <= 3_000_000,
        )
    )

    avg_payment_raw = (
        overview.get("average_monthly_payment", _MISSING)
        if overview is not _MISSING
        else _MISSING
    )

    income_item = next(
        (
            item
            for item in reversed(incomes.get("monthly") or [])
            if (item.get("amount") or 0) > 0
        ),
        {},
    )
    last_non_zero_income = float(income_item.get("amount") or 0)

    if (
        avg_payment_raw is _MISSING
        or avg_payment_raw is None
        or last_non_zero_income <= 0
    ):
        results.append(
            {
                "key": t["rule_katm_lti"],
                "value": t["no_data"],
                "status": "no_data",
            }
        )
    else:
        average_monthly_payment = float(avg_payment_raw or 0)
        ratio = average_monthly_payment / last_non_zero_income
        results.append(
            {
                "key": t["rule_katm_lti"],
                "value": f"{ratio * 100:.1f}% ({last_non_zero_income:,.1f})",
                "status": "pass" if ratio <= 0.3 else "fail",
            }
        )

    return results


def save_verification_history(pinfl, req_type, results):
    """Helper function to save report and items into database"""
    if not results:
        return
    report = VerificationReport.objects.create(pinfl=pinfl, check_type=req_type)
    items_to_create = [
        VerificationItem(
            report=report,
            title=res["key"],
            value_display=str(res["value"]),
            status=res["status"],
        )
        for res in results
    ]
    VerificationItem.objects.bulk_create(items_to_create)


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
                    results = evaluate_mib(pinfl, t)
                    context["results"] = results
                    save_verification_history(pinfl, req_type, results)
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
                    pinfl = (
                        katm_data.get("credit_information_subject") or {}
                    ).get("personal_id_number")

                    if not pinfl:
                        context["error"] = t["err_no_pinfl_in_pdf"]
                    else:
                        context["pinfl_val"] = pinfl
                        katm_results = evaluate_katm(katm_data, t)
                        mib_results = evaluate_mib(str(pinfl), t)
                        results = katm_results + mib_results
                        context["results"] = results
                        save_verification_history(str(pinfl), req_type, results)
                except Exception as e:
                    context["error"] = f"{t['err_katm_prefix']}{str(e)}"

    return render(request, "main.html", context)


@login_not_required
class CustomLoginView(LoginView):
    template_name = "login.html"
    redirect_authenticated_user = True


def profile(request):
    lang = request.GET.get("lang") or "ru"
    if lang not in TRANSLATIONS:
        lang = "ru"

    t = TRANSLATIONS[lang]

    # Fetch user's reports history ordered by newest first
    reports_list = (
        VerificationReport.objects.prefetch_related("items")
        .all()
        .order_by("-created_at")
    )

    # Setup pagination: 10 reports per page
    paginator = Paginator(reports_list, 10)
    page_number = request.GET.get("page")
    reports = paginator.get_page(page_number)

    context = {
        "t": t,
        "lang": lang,
        "reports": reports,  # Page object containing the reports
    }

    return render(request, "profile.html", context)


def score(request):
    lang = request.GET.get("lang") or "ru"
    if lang not in TRANSLATIONS:
        lang = "ru"

    t = TRANSLATIONS[lang]

    if request.method == 'GET':
        if request.GET.get('pinfl', None) == None:
            return redirect('main')
        context = {
            "t": t,
            "lang": lang,
            "pinfl_val": request.GET.get('pinfl')
        }
        return render(request, "application.html", context)

    if request.method == 'POST':
        p = request.POST
        f = lambda k, d=0.0: float(str(p.get(k, d) or d).replace(' ', '').replace('\xa0', '').replace(',', '.'))

        # Convert date to DD.MM.YYYY format
        raw_date = p.get('birth_date', '').strip()
        date_birth = ''
        if raw_date:
            try:
                # Handles '1987-08-10' -> '10.08.1987'
                date_birth = datetime.strptime(raw_date, '%Y-%m-%d').strftime('%d.%m.%Y')
            except ValueError:
                date_birth = raw_date  # Keep as-is if already in DD.MM.YYYY

        payload = {
            "category": p.get('category', '').strip(),
            "sub_category": p.get('subcategory', '').strip(),
            "brand": p.get('brand', '').strip(),
            "region": p.get('region', '').strip(),
            "income_source": p.get('income_source', '').strip(),
            "gender": p.get('gender', '').strip(),
            "client_type": p.get('client_type', '').strip(),
            "date_birth": date_birth,  # Correctly formatted: DD.MM.YYYY
            "mfy_name": p.get('mfi_name', '').strip(),
            "job": p.get('job'),
            "pinfl": p.get('pinfl', '').strip(),
            "loan_period": int(p.get('term_months') or 1),
            "quantity": int(p.get('quantity') or 1),
            "product_price": f('price'),
            "prepayment_amount": f('initial_payment'),
            "monthly_payment": f('monthly_payment'),
            "additional_income": f('additional_income'),
            "interest_rate": f('rate_percent'),
            "monthly_income": f('monthly_income'),
        }

        url = "https://barakasavdo.moliy.ai/api/predict"

        try:
            res = requests.post(
                url,
                data=payload,
                auth=("filial3admin", "GE11w6sFNsJ5"),
                timeout=30
            )

            # 1. Check HTTP Status Code
            if not res.ok:
                try:
                    err_msg = res.json().get('detail') or res.json().get('message') or res.text
                except Exception:
                    err_msg = res.text
                return render(request, 'score.html', {'error': f"API Error ({res.status_code}): {err_msg}"})

            # 2. Parse JSON
            resp_json = res.json()

            # 3. Safely extract prediction without KeyError
            prediction = resp_json.get('data', {}).get('prediction') if isinstance(resp_json, dict) else None

            if prediction is None:
                return render(request, 'score.html', {'error': f"Unexpected response format: {resp_json}"})

            return render(request, 'score.html', {'data': prediction})

        except requests.exceptions.Timeout:
            return render(request, 'score.html', {'error': "Время ожидания ответа от сервера скоринга истекло (Timeout)."})
        except requests.exceptions.RequestException as e:
            return render(request, 'score.html', {'error': f"Ошибка соединения с сервисом скоринга: {e}"})
        except Exception as e:
            return render(request, 'score.html', {'error': f"Непредвиденная ошибка: {e}"})

        return render(request, 'score.html', {'data': data})


def score_response(request):
    context = {
        "score": 0.78,
        "decisiion": "Approve"
    }
    return render(request, "")
