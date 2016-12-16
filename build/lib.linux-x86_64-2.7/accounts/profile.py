from .models import UserProfile
from .forms import UserProfileForm

def retrieve(request):
    """ note that this required an authenticated
    user before we try calling it """
    try:
        profile = request.user.get_profile()
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    finally:
        return profile

def set(request):
    """
    retieves the profile of the current user, binds the data
    that comes in from a POST request to the user's instance of 
    their profile data and saves it to the database
    """
    profile      = retrieve(request)
    profile_form = UserProfileForm(request.POST, instance=profile)
    profile_form.save() 
    
