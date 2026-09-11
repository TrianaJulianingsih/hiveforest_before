from django import forms
from apps.base.models.userprofiles import UserProfile
from apps.base.models.people import Person

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'bio']
        
    def clean_profile_picture(self):
        picture = self.cleaned_data.get('profile_picture', False)
        if picture:
            if picture.size > 2 * 1024 * 1024:  # 2MB limit
                raise forms.ValidationError("Image file too large ( > 2MB )")
            if not picture.content_type in ['image/jpeg', 'image/png']:
                raise forms.ValidationError("Invalid image format (only JPEG and PNG are supported).")
        return picture
    
class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = '__all__'
        widgets = {
            "roles": forms.SelectMultiple(attrs={"size": 10, "style": "width: 300px;"}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove "add/change" related widget options for these fields
        for field_name in ['gender', 'salutation']:
            if field_name in self.fields:
                self.fields[field_name].widget.can_add_related = False
                self.fields[field_name].widget.can_change_related = False
                self.fields[field_name].widget.can_view_related = False
                self.fields[field_name].widget.can_delete_related = False