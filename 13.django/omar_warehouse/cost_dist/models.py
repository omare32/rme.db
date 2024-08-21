from django.db import models

# Create your models here.


class CostDist(models.Model):
    project_no = models.CharField(max_length=50, unique=True) 
    project_name = models.CharField(max_length=200)
    gl_date = models.DateField()
    line_desc = models.CharField(max_length=200)
    unit = models.CharField(max_length=50)
    qty = models.DecimalField(max_digits=10, decimal_places=2)  # Adjust max_digits and decimal_places as needed
    amount = models.DecimalField(max_digits=15, decimal_places=2)  # Adjust max_digits and decimal_places as needed

    def __str__(self):
        return f"{self.project_no} - {self.project_name}" 