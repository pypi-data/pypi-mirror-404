from django.db import models

class PaymentVerification(models.Model):
    order_id = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20)  # e.g., "success" or "failed"
    paid_at = models.DateTimeField(auto_now=False, null=True)

    def __str__(self):
        return f"{self.order_id} - {self.status}"

class SymbolSettings(models.Model):
    symbol = models.CharField(max_length=20)
    lot_size = models.FloatField()
    max_trades = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.symbol} | lot={self.lot_size} | trades={self.max_trades}"
    
