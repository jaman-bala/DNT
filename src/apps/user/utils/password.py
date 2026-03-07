# Логика для смены пароля кадый месяц 
from django.utils import timezone
from apps.user.models.users import User

def is_password_change_required(user: User) -> bool:
    """
    Returns True if the user is required to change their password.
    Password change is required on the 1st day of every month.
    """
    if not user or not user.is_authenticated:
        return False
        
    now = timezone.now()
    
    # Requirement: 1st day of the month
    if now.day != 1:
        return False
        
    # If the password was changed before today (which is the 1st), it needs changing
    # We compare dates to ensure that if they changed it today (the 1st), they are done.
    if user.password_changed_at:
        return user.password_changed_at.date() < now.date()
        
    return True