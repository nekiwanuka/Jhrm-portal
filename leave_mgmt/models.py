from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class LeaveType(models.Model):

    name = models.CharField(max_length=100, unique=True)
    code = models.SlugField(
        max_length=40,
        unique=True,
        null=True,
        blank=True,
        help_text='Short unique code, e.g. annual, sick, maternity',
    )
    max_days_per_year = models.PositiveIntegerField(default=21)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name


class LeaveRequest(models.Model):

    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_leave_requests',
    )
    decision_notes = models.TextField(blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError('End date must be after or equal to start date.')
        if self.start_date and self.end_date and self.start_date.year != self.end_date.year:
            raise ValidationError('Leave request must be within the same calendar year.')

        # Prevent overlapping requests for the same employee (pending or approved)
        if self.employee_id and self.start_date and self.end_date:
            overlap_qs = LeaveRequest.objects.filter(employee_id=self.employee_id).exclude(pk=self.pk)
            overlap_qs = overlap_qs.filter(status__in=[self.STATUS_PENDING, self.STATUS_APPROVED])
            overlap_qs = overlap_qs.filter(Q(start_date__lte=self.end_date) & Q(end_date__gte=self.start_date))
            if overlap_qs.exists():
                raise ValidationError('This leave request overlaps an existing pending/approved request.')

        # Enforce entitlement per year using approved leave days
        if self.leave_type_id and self.start_date and self.end_date:
            max_days = self.leave_type.max_days_per_year
            year = self.start_date.year
            approved = LeaveRequest.objects.filter(
                employee_id=self.employee_id,
                leave_type_id=self.leave_type_id,
                status=self.STATUS_APPROVED,
                start_date__year=year,
            ).exclude(pk=self.pk)
            approved_days = sum(r.total_days for r in approved)
            requested_days = self.total_days
            if approved_days + requested_days > max_days:
                raise ValidationError(f'Request exceeds entitlement. Remaining days: {max_days - approved_days}.')

    @property
    def total_days(self):
        return (self.end_date - self.start_date).days + 1

    def __str__(self):
        return f'{self.employee} - {self.leave_type} ({self.status})'
