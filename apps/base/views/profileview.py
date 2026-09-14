from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from apps.base.forms.profileforms import UserProfileForm

@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        print(request.FILES)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'profile.html', {'form': form})