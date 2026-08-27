from django.db import models


class VerificationReport(models.Model):
    pinfl = models.CharField(max_length=14, verbose_name="ПИНФЛ")
    check_type = models.CharField(
        max_length=50, verbose_name="Тип проверки"
    )  # 'pinfl' or 'katm_pdf'
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата проверки"
    )

    class Meta:
        verbose_name = "Отчет проверки"
        verbose_name_plural = "Отчеты проверок"
        ordering = ["-created_at"]

    def __str__(self):
        return f"ПИНФЛ: {self.pinfl} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"


class VerificationItem(models.Model):
    report = models.ForeignKey(
        VerificationReport,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Отчет",
    )
    title = models.CharField(max_length=255, verbose_name="Критерий")
    value_display = models.CharField(max_length=255, verbose_name="Значение")
    status = models.CharField(
        max_length=50, verbose_name="Статус"
    )  # 'pass', 'fail', 'no_data'

    class Meta:
        verbose_name = "Элемент проверки"
        verbose_name_plural = "Элементы проверок"

    def __str__(self):
        return f"{self.title}: {self.value_display} [{self.status}]"
